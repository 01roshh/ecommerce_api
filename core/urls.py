from django.urls import path
from .views import (
    UserRegisterView, 
    ProductListViewSet, ProductDetailViewSet, ProductCreateViewSet,
    CartDetailViewSet, AddToCartView, UpdateCartItemView, RemoveFromCartView,
    OrderListView, OrderDetailView, CreateOrderView, CancelOrderView, CheckoutView, CheckoutAllOrdersView
)


urlpatterns = [
    path('auth/register/', UserRegisterView.as_view(), name='register'),
    # Products
    path('products/', ProductListViewSet.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailViewSet.as_view(), name='product-detail'),
    path('products/create/', ProductCreateViewSet.as_view(), name='product-create'),

    # Cart
    path('cart/', CartDetailViewSet.as_view(), name='cart-detail'),
    path('cart/add/', AddToCartView.as_view(), name='add-to-cart'),
    path('cart/update/<int:item_id>/', UpdateCartItemView.as_view(), name='update-cart-item'),
    path('cart/remove/<int:item_id>/', RemoveFromCartView.as_view(), name='remove-from-cart'),
    
    # Orders
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/create/', CreateOrderView.as_view(), name='create-order'),
    path('orders/cancel/<int:pk>/', CancelOrderView.as_view(), name='cancel-order'),
    path('orders/checkout/<int:pk>/', CheckoutView.as_view(), name='checkout-order'),
    path('orders/checkout/all/', CheckoutAllOrdersView.as_view(), name='checkout-all-orders'),
]