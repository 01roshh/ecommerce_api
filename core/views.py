from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Q, Avg
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

import stripe
from django.conf import settings
from django.core.cache import cache

from .models import (
    Product, Cart, Order, CartItem, OrderItem,
    UserProfile, Review, Coupon, Wishlist, OrderCoupon
)
from .serializers import (
    UserRegisterSerializer, ProductSerializer, CartSerializer,
    OrderSerializer, CartItemSerializer, OrderItemSerializer,
    UserProfileSerializer, ReviewSerializer, CouponSerializer,
    WishlistSerializer, AddToCartRequestSerializer, UpdateCartItemRequestSerializer,
    CreateOrderRequestSerializer, ConfirmPaymentRequestSerializer,
    ValidateCouponRequestSerializer, WishlistActionRequestSerializer
)
from .permissions import IsCartOwner, IsOrderOwner, CanCancelOrder

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY

# ==================== AUTH & PROFILE ====================

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Product.objects.values_list('category', flat=True).distinct()
        return Response(list(categories))

# ==================== PRODUCT VIEWS ====================

class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "category"]
    ordering_fields = ["price", "rating", "created_at"]
    ordering = ["-created_at"]

    def list(self, request, *args, **kwargs):
        # Cache disabled temporarily for debugging; reactive for production if needed
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        
        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        in_stock = self.request.query_params.get("in_stock")
        if in_stock:
            queryset = queryset.filter(stock__gt=0)
            
        return queryset

class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        cache_key = f"product_detail_{pk}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=600)
        return response

class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

class ProductAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

# ==================== CART VIEWS ====================

class CartDetailView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

class AddToCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=AddToCartRequestSerializer,
        responses={201: CartItemSerializer, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = AddToCartRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
            
        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data.get("quantity", 1)
        
        product = get_object_or_404(Product, id=product_id)
        
        if product.stock < quantity:
            return Response({"error": f"Insufficient stock for {product.name}. Available: {product.stock}"}, status=400)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response(CartItemSerializer(cart_item).data, status=201)

class UpdateCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=UpdateCartItemRequestSerializer,
        responses={200: CartItemSerializer, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    def put(self, request, item_id):
        serializer = UpdateCartItemRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        quantity = serializer.validated_data["quantity"]
        
        cart = get_object_or_404(Cart, user=request.user)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

        if quantity <= 0:
            cart_item.delete()
            return Response(status=204)

        if cart_item.product.stock < quantity:
            return Response({"error": f"Insufficient stock for {cart_item.product.name}. Available: {cart_item.product.stock}"}, status=400)

        cart_item.quantity = quantity
        cart_item.save()
        return Response(CartItemSerializer(cart_item).data)

class RemoveFromCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response(status=204)

# ==================== ORDER VIEWS ====================

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwner]
    queryset = Order.objects.all()

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=CreateOrderRequestSerializer,
        responses={201: OrderSerializer, 400: OpenApiTypes.OBJECT}
    )
    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        # Validate stock before processing
        for item in cart_items:
            if item.quantity > item.product.stock:
                return Response({"error": f"Insufficient stock for {item.product.name}"}, status=400)

        user_profile = get_object_or_404(UserProfile, user=request.user)
        v_data = serializer.validated_data
        
        order = Order.objects.create(
            user=request.user,
            status="pending",
            shipping_address=v_data.get("address", user_profile.address),
            shipping_city=v_data.get("city", user_profile.city),
            shipping_state=v_data.get("state", user_profile.state),
            shipping_postal_code=v_data.get("postal_code", user_profile.postal_code),
            shipping_country=v_data.get("country", user_profile.country),
        )

        total_price = 0
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
            )
            # Deduct stock
            cart_item.product.reduce_stock(cart_item.quantity)
            total_price += float(cart_item.product.price) * cart_item.quantity

        order.total_price = total_price
        order.final_price = total_price
        
        # Coupon Logic
        coupon_code = v_data.get("coupon_code")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                now = timezone.now()
                if coupon.valid_from <= now <= coupon.valid_to:
                    if float(total_price) >= float(coupon.min_order_amount):
                        discount = float(total_price * coupon.discount_percent / 100) if coupon.discount_percent else float(coupon.discount_amount)
                        order.discount_price = discount
                        order.final_price = total_price - discount
                        OrderCoupon.objects.create(order=order, coupon=coupon, discount_amount=discount)
            except Coupon.DoesNotExist:
                pass

        order.save()
        cart_items.delete()

        return Response(OrderSerializer(order).data, status=201)

class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    @transaction.atomic
    def post(self, request, pk=None):
        # If no pk is provided in URL, try to get the user's latest pending order
        if pk is None:
            order = Order.objects.filter(user=request.user, status="pending").first()
            if not order:
                return Response({"error": "No pending order found. Please create an order from your cart first."}, status=404)
        else:
            order = get_object_or_404(Order, pk=pk, user=request.user)
        
        if order.status not in ["pending", "payment_pending"]:
            return Response({"error": f"Order #{order.id} is in '{order.status}' status and cannot be checked out."}, status=400)

        if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY == "sk_test_placeholder":
            return Response({"error": "Stripe Secret Key is not configured in .env"}, status=500)

        try:
            # If order already has a processing payment, we check if we can reuse it
            if order.payment_id:
                try:
                    intent = stripe.PaymentIntent.retrieve(order.payment_id)
                    if intent.status == "succeeded":
                        order.payment_status = "completed"
                        order.status = "processing"
                        order.save()
                        return Response({"message": "Order already paid", "order": OrderSerializer(order).data})
                    return Response({"client_secret": intent.client_secret, "payment_id": intent.id, "order_id": order.id})
                except stripe.error.StripeError:
                    pass

            intent = stripe.PaymentIntent.create(
                amount=int(float(order.final_price) * 100),
                currency="usd",
                metadata={"order_id": order.id, "user_email": request.user.email},
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            )
            order.payment_id = intent.id
            order.payment_status = "pending"
            order.status = "payment_pending"
            order.save()
            return Response({
                "client_secret": intent.client_secret, 
                "payment_id": intent.id,
                "order_id": order.id,
                "amount": order.final_price
            })
        except Exception as e:
            return Response({"error": f"Stripe Error: {str(e)}"}, status=400)

class ConfirmPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ConfirmPaymentRequestSerializer,
        responses={200: OrderSerializer, 400: OpenApiTypes.OBJECT}
    )
    @transaction.atomic
    def post(self, request):
        serializer = ConfirmPaymentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
            
        payment_id = serializer.validated_data.get("payment_id")
        order_id = serializer.validated_data.get("order_id")
        test_accept = serializer.validated_data.get("test_accept", False)
        
        order = get_object_or_404(Order, id=order_id, user=request.user, payment_id=payment_id)
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_id)
            
            # SIMULATION: If test_accept is true and we are in DEBUG mode, 
            # we manually confirm the intent using a test card.
            if test_accept and settings.DEBUG and intent.status == "requires_payment_method":
                intent = stripe.PaymentIntent.confirm(
                    payment_id,
                    payment_method="pm_card_visa",
                )

            if intent.status == "succeeded":
                order.payment_status = "completed"
                order.status = "processing"
                order.save()
                
                # Increment coupon usage if exists
                try:
                    order_coupon = OrderCoupon.objects.get(order=order)
                    coupon = order_coupon.coupon
                    if coupon:
                        coupon.used_count += 1
                        coupon.save()
                except OrderCoupon.DoesNotExist:
                    pass

                return Response({"message": "Payment successful", "order": OrderSerializer(order).data})
            return Response({"error": f"Payment status: {intent.status}. (Tip: Use test_accept=true to simulate payment in DEBUG mode)"}, status=400)
        except Exception as e:
            return Response({"error": f"Stripe Error: {str(e)}"}, status=400)

class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanCancelOrder]

    @transaction.atomic
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status not in ['pending', 'payment_pending']:
            return Response({"error": "Only pending or payment-pending orders can be canceled"}, status=400)
            
        order.status = "canceled"
        order.save()

        # Restore stock
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

        return Response({"message": "Order canceled"})

# ==================== WISHLIST VIEWS ====================

class WishlistView(generics.RetrieveAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        wishlist, _ = Wishlist.objects.get_or_create(user=self.request.user)
        return wishlist

class AddToWishlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=WishlistActionRequestSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = WishlistActionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
            
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        product_id = serializer.validated_data["product_id"]
        product = get_object_or_404(Product, id=product_id)
        wishlist.products.add(product)
        return Response({"message": "Added to wishlist"})

class RemoveFromWishlistView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=WishlistActionRequestSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = WishlistActionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
            
        wishlist = get_object_or_404(Wishlist, user=request.user)
        product_id = serializer.validated_data["product_id"]
        product = get_object_or_404(Product, id=product_id)
        wishlist.products.remove(product)
        return Response({"message": "Removed from wishlist"})

# ==================== REVIEW VIEWS ====================

class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs["product_id"]).order_by("-created_at")

class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs["product_id"])
        serializer.save(user=self.request.user, product=product)
        
        # Update product rating
        avg_rating = Review.objects.filter(product=product).aggregate(Avg("rating"))["rating__avg"]
        product.rating = avg_rating or 0
        product.review_count = Review.objects.filter(product=product).count()
        product.save()

# ==================== COUPON VIEWS ====================

class CouponListView(generics.ListAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]

class CouponCreateView(generics.CreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]

class ValidateCouponView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ValidateCouponRequestSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        serializer = ValidateCouponRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        code = serializer.validated_data["code"]
        total_price = float(serializer.validated_data["total_price"])
        
        coupon = get_object_or_404(Coupon, code=code, is_active=True)
        
        now = timezone.now()
        if not (coupon.valid_from <= now <= coupon.valid_to):
            return Response({"error": "Coupon expired"}, status=400)
            
        if total_price < float(coupon.min_order_amount):
            return Response({"error": f"Minimum order amount is {coupon.min_order_amount}"}, status=400)

        if coupon.max_uses and coupon.used_count >= coupon.max_uses:
            return Response({"error": "Coupon use limit reached"}, status=400)

        discount = float(total_price * coupon.discount_percent / 100) if coupon.discount_percent else float(coupon.discount_amount)
        return Response({
            "valid": True,
            "discount": discount,
            "final_price": total_price - discount
        })