import os
import django
from django.utils import timezone
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Product, Coupon
from django.contrib.auth import get_user_model

User = get_user_model()

def seed_data():
    print("Seeding sample data...")
    
    # Create Admin
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True}
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print("- Admin user created (admin / admin123)")

    # Create Sample Products
    products = [
        {
            "name": "High-Performance Laptop",
            "description": "Powerful laptop for gaming and development with 32GB RAM.",
            "price": Decimal("1299.99"),
            "stock": 50,
            "category": "Electronics"
        },
        {
            "name": "Wireless Noise-Canceling Headphones",
            "description": "Premium sound quality with active noise cancellation.",
            "price": Decimal("299.00"),
            "stock": 100,
            "category": "Electronics"
        },
        {
            "name": "Organic Cotton T-Shirt",
            "description": "Comfortable, sustainable fashion in various colors.",
            "price": Decimal("24.50"),
            "stock": 500,
            "category": "Apparel"
        },
        {
            "name": "Mechanical Gaming Keyboard",
            "description": "RGB backlit keyboard with tactile switches.",
            "price": Decimal("89.99"),
            "stock": 75,
            "category": "Electronics"
        }
    ]

    for p_data in products:
        Product.objects.get_or_create(
            name=p_data["name"],
            defaults={
                "description": p_data["description"],
                "price": p_data["price"],
                "stock": p_data["stock"],
                "category": p_data["category"]
            }
        )
    print(f"- {len(products)} products seeded.")

    # Create Sample Coupons
    Coupon.objects.get_or_create(
        code="WELCOME10",
        defaults={
            "description": "10% off for new users",
            "discount_percent": 10,
            "valid_from": timezone.now(),
            "valid_to": timezone.now() + timezone.timedelta(days=365),
            "is_active": True,
            "min_order_amount": 50
        }
    )
    print("- Coupon 'WELCOME10' seeded.")

if __name__ == "__main__":
    seed_data()
    print("Seed complete!")
