from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Product, UserProfile, Cart, CartItem, 
    Order, OrderItem, Review, Coupon, 
    Wishlist, OrderCoupon
)

# Define an inline admin descriptor for UserProfile model
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

# Custom form for creating users with an email right away
class UserCreationForm(BaseUserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = BaseUserCreationForm.Meta.fields + ("email",)

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm # Use our custom form for the "Add User" page
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    
    # Merge email into the main fieldset for proper design alignment
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')

class OrderCouponInline(admin.StackedInline):
    model = OrderCoupon
    extra = 0
    readonly_fields = ('coupon', 'discount_amount', 'applied_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'rating', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    ordering = ('-created_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    inlines = [CartItemInline]
    search_fields = ('user__username',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'final_price', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline, OrderCouponInline]
    search_fields = ('user__username', 'payment_id')
    readonly_fields = ('payment_id', 'created_at', 'updated_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'discount_amount', 'is_active', 'valid_to', 'used_count')
    list_filter = ('is_active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    filter_horizontal = ('products',)
    search_fields = ('user__username',)