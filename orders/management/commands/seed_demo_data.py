from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.management.demo_data import DEMO_PRODUCTS, DEMO_PROMOS, DEMO_USERS
from orders.models import Product
from promotions.models import PromoCode, UserPromoUsage

User = get_user_model()


class Command(BaseCommand):
    """Create demo users, products, and promo codes for manual API testing."""

    help = "Create demo users, products, and promo codes."

    def handle(self, *args, **options) -> None:
        users = [
            User.objects.update_or_create(id=user_id, defaults={"username": username})[0]
            for user_id, username in DEMO_USERS
        ]

        products = [
            Product.objects.update_or_create(
                id=product_data["id"],
                defaults={
                    "name": product_data["name"],
                    "price": product_data["price"],
                    "category": product_data["category"],
                    "is_excluded_from_promotions": product_data["is_excluded_from_promotions"],
                },
            )[0]
            for product_data in DEMO_PRODUCTS
        ]

        now = timezone.now()
        promo_codes = [
            PromoCode.objects.update_or_create(
                code=promo_data["code"],
                defaults={
                    "discount_percent": promo_data["discount_percent"],
                    "max_usages": promo_data["max_usages"],
                    "valid_until": now + timedelta(days=promo_data["valid_for_days"]),
                    "allowed_categories": promo_data["allowed_categories"],
                    "current_usages": 0,
                },
            )[0]
            for promo_data in DEMO_PROMOS
        ]

        UserPromoUsage.objects.filter(user__in=users, promocode__in=promo_codes).delete()

        self.stdout.write("Users:")
        for user in users:
            self.stdout.write(f"  id={user.id}, username={user.username}")

        self.stdout.write("Goods:")
        for product in products:
            promo_status = "excluded from promos" if product.is_excluded_from_promotions else "promo applies"
            self.stdout.write(f"  id={product.id}, category={product.category}, {promo_status}")

        self.stdout.write("Promo codes:")
        for promo in promo_codes:
            categories = promo.allowed_categories or "all"
            promo_status = "expired" if promo.valid_until < now else "active"
            self.stdout.write(
                f"  {promo.code}: {promo.discount_percent}%, categories={categories}, {promo_status}"
            )
