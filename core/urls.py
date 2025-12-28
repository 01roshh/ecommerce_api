from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("auth/register/", views.UserRegisterView.as_view(), name="register"),
    
    # Profile
    path("profile/", views.UserProfileView.as_view(), name="user-profile"),

    # Products
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("products/create/", views.ProductCreateView.as_view(), name="product-create"),
    path("products/admin/<int:pk>/", views.ProductAdminDetailView.as_view(), name="product-admin-detail"),
    
    # Reviews
    path("products/<int:product_id>/reviews/", views.ReviewListView.as_view(), name="review-list"),
    path("products/<int:product_id>/reviews/create/", views.ReviewCreateView.as_view(), name="review-create"),

    # Cart
    path("cart/", views.CartDetailView.as_view(), name="cart-detail"),
    path("cart/add/", views.AddToCartView.as_view(), name="add-to-cart"),
    path("cart/update/<int:item_id>/", views.UpdateCartItemView.as_view(), name="update-cart-item"),
    path("cart/remove/<int:item_id>/", views.RemoveFromCartView.as_view(), name="remove-from-cart"),

    # Wishlist
    path("wishlist/", views.WishlistView.as_view(), name="wishlist"),
    path("wishlist/add/", views.AddToWishlistView.as_view(), name="add-to-wishlist"),
    path("wishlist/remove/", views.RemoveFromWishlistView.as_view(), name="remove-from-wishlist"),

    # Coupons
    path("coupons/", views.CouponListView.as_view(), name="coupon-list"),
    path("coupons/create/", views.CouponCreateView.as_view(), name="coupon-create"),
    path("coupons/validate/", views.ValidateCouponView.as_view(), name="validate-coupon"),

    # Orders
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("orders/create/", views.CreateOrderView.as_view(), name="create-order"),
    path("orders/checkout/", views.CheckoutView.as_view(), name="checkout-order-latest"),
    path("orders/<int:pk>/checkout/", views.CheckoutView.as_view(), name="checkout-order"),
    path("orders/confirm-payment/", views.ConfirmPaymentView.as_view(), name="confirm-payment"),
    path("orders/<int:order_id>/cancel/", views.CancelOrderView.as_view(), name="cancel-order"),
]
