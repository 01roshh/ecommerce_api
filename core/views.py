from django.shortcuts import render, get_object_or_404
from .models import Product, Cart, Order, CartItem, OrderItem
from .serializers import UserRegisterSerializer, ProductSerializer, CartSerializer, OrderSerializer, CartItemSerializer, OrderItemSerializer
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import generics, permissions, status
from .permissions import IsCartOwner, IsOrderOwner, CanCancelOrder

User = get_user_model()

# Create your views here.
class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = []
 
class ProductListViewSet(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    
class ProductDetailViewSet(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    
class ProductCreateViewSet(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can create products

class CartDetailViewSet(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsCartOwner]  # Added IsCartOwner
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

class AddToCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id)
       
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        
        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return JsonResponse({"message": "Item added to cart", "cart_item": serializer.data})

class UpdateCartItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({"message": "Cart item removed"}, status=204)

        cart_item.quantity = quantity
        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return JsonResponse({"message": "Cart item updated", "cart_item": serializer.data})

class RemoveFromCartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return JsonResponse({"message": "Cart item removed"}, status=204)

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
    

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwner]  # Added IsOrderOwner
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user) 

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Get the user's cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return JsonResponse({"message": "Cart not found"}, status=404)
        
        # Get all cart items for this cart
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            return JsonResponse({"message": "Cart is empty"}, status=400)

        # Create the order
        order = Order.objects.create(user=request.user, status='pending')
        
        # Create order items from cart items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Clear the cart
        cart_items.delete()
        
        serializer = OrderSerializer(order)
        return JsonResponse({"message": "Order created successfully", "order": serializer.data}, status=201)

class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanCancelOrder]
    
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # The CanCancelOrder permission already checks if the order is pending
        # and if the user owns the order
        order.status = 'canceled'
        order.save()
        
        # Restore product stock
        for order_item in order.orderitem_set.all():
            order_item.product.stock += order_item.quantity
            order_item.product.save()
        
        serializer = OrderSerializer(order)
        return JsonResponse({"message": "Order canceled", "order": serializer.data})

class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        
        # Add your payment processing logic here
        # For now, just update status to 'completed'
        order.status = 'completed'
        order.save()
        
        serializer = OrderSerializer(order)
        return JsonResponse({"message": "Order completed successfully", "order": serializer.data})
    
class CheckoutAllOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Get all pending orders for the current user
        pending_orders = Order.objects.filter(user=request.user, status='pending')
        
        if not pending_orders.exists():
            return JsonResponse({"message": "No pending orders found"}, status=404)
        
        completed_orders = []
        
        # Checkout each pending order
        for order in pending_orders:
            order.status = 'completed'
            order.save()
            completed_orders.append(order.id)
        
        return JsonResponse({
            "message": f"Successfully checked out {len(completed_orders)} orders",
            "completed_order_ids": completed_orders
        }, status=200)