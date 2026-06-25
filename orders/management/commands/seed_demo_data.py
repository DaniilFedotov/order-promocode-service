from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Product
from promotions.models import PromoCode, UserPromoUsage

User = get_user_model()

DEMO_USERS = [
    (1, "demo_user_1"),
    (2, "demo_user_2"),
    (3, "demo_user_3"),
    (4, "demo_user_4"),
    (5, "demo_user_5"),
]

DEMO_PROMOS = [
    {
        "code": "SUMMER2025",
        "discount_percent": 10,
        "max_usages": 100,
        "valid_for_days": 30,
        "allowed_categories": ["clothes"],
    },
    {
        "code": "ALL20",
        "discount_percent": 20,
        "max_usages": 100,
        "valid_for_days": 30,
        "allowed_categories": [],
    },
    {
        "code": "OLD2020",
        "discount_percent": 10,
        "max_usages": 100,
        "valid_for_days": -1,
        "allowed_categories": [],
    },
]


class Command(BaseCommand):
    """Create demo users, products, and promo codes for manual API testing."""

    help = "Create demo users, products, and promo codes."

    def handle(self, *args, **options):
        """Insert or update demo records, reset promo usage, and print a summary."""
        users = []
        for user_id, username in DEMO_USERS:
            user, _ = User.objects.update_or_create(
                id=user_id,
                defaults={"username": username},
            )
            users.append(user)

        shirt, _ = Product.objects.update_or_create(
            id=1,
            defaults={
                "name": "T-shirt",
                "price": Decimal("100.00"),
                "category": "clothes",
            },
        )
        book, _ = Product.objects.update_or_create(
            id=2,
            defaults={
                "name": "Book",
                "price": Decimal("50.00"),
                "category": "books",
                "is_excluded_from_promotions": True,
            },
        )
        notebook, _ = Product.objects.update_or_create(
            id=3,
            defaults={
                "name": "Notebook",
                "price": Decimal("30.00"),
                "category": "stationery",
            },
        )

        promo_codes = []
        now = timezone.now()
        for promo_data in DEMO_PROMOS:
            valid_until = now + timedelta(days=promo_data["valid_for_days"])
            promo, _ = PromoCode.objects.update_or_create(
                code=promo_data["code"],
                defaults={
                    "discount_percent": promo_data["discount_percent"],
                    "max_usages": promo_data["max_usages"],
                    "valid_until": valid_until,
                    "allowed_categories": promo_data["allowed_categories"],
                    "current_usages": 0,
                },
            )
            promo_codes.append(promo)

        UserPromoUsage.objects.filter(
            user__in=users,
            promocode__in=promo_codes,
        ).delete()

        self.stdout.write("Users:")
        for user in users:
            self.stdout.write(f"  id={user.id}, username={user.username}")

        self.stdout.write("Goods:")
        self.stdout.write(f"  id={shirt.id}, category=clothes, promo applies")
        self.stdout.write(f"  id={book.id}, category=books, excluded from promos")
        self.stdout.write(f"  id={notebook.id}, category=stationery, promo applies")

        self.stdout.write("Promo codes:")
        for promo in promo_codes:
            categories = promo.allowed_categories or "all"
            status = "expired" if promo.valid_until < timezone.now() else "active"
            self.stdout.write(
                f"  {promo.code}: {promo.discount_percent}%, categories={categories}, {status}"
            )
