from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Product,
    Cart,
    Order,
    CartItem,
    OrderItem,
    UserProfile,
    Review,
    Coupon,
    Wishlist,
    OrderCoupon,
)

User = get_user_model()


class AddToCartRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)


class UpdateCartItemRequestSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderRequestSerializer(serializers.Serializer):
    address = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    coupon_code = serializers.CharField(required=False)


class ConfirmPaymentRequestSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    order_id = serializers.IntegerField()
    test_accept = serializers.BooleanField(required=False, default=False)


class ValidateCouponRequestSerializer(serializers.Serializer):
    code = serializers.CharField()
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class WishlistActionRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email"),
            password=validated_data["password"],
        )
        # Create profile for new user
        UserProfile.objects.create(user=user)
        Cart.objects.create(user=user)
        Wishlist.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "username",
            "email",
            "phone",
            "address",
            "city",
            "state",
            "postal_code",
            "country",
            "profile_picture",
            "date_of_birth",
        ]


class ProductSerializer(serializers.ModelSerializer):
    formatted_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "formatted_price",
            "stock",
            "category",
            "image",
            "rating",
            "review_count",
            "created_at",
            "updated_at",
        ]

    def get_formatted_price(self, obj):
        return f"${obj.price:,.2f}"



class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "username",
            "rating",
            "title",
            "comment",
            "helpful_count",
            "created_at",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(source="cart_items", many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items", "user"]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "description",
            "discount_percent",
            "discount_amount",
            "min_order_amount",
            "max_uses",
            "used_count",
            "valid_from",
            "valid_to",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["used_count", "created_at"]


class OrderCouponSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="coupon.code", read_only=True)
    description = serializers.CharField(source="coupon.description", read_only=True)

    class Meta:
        model = OrderCoupon
        fields = ["code", "description", "discount_amount"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    coupon = OrderCouponSerializer(read_only=True)
    formatted_total_price = serializers.SerializerMethodField()
    formatted_final_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "total_price",
            "formatted_total_price",
            "discount_price",
            "final_price",
            "formatted_final_price",
            "shipping_address",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "payment_id",
            "payment_method",
            "payment_status",
            "coupon",
            "items",
            "created_at",
        ]
        read_only_fields = ["user", "payment_id", "final_price", "total_price"]

    def get_formatted_total_price(self, obj):
        return f"${obj.total_price:,.2f}"

    def get_formatted_final_price(self, obj):
        return f"${obj.final_price:,.2f}"


class WishlistSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        
        fields = ["id","products","user", "status", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]
