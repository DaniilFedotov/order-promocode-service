from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from orders.models import Product
from promotions.models import PromoCode, UserPromoUsage
from promotions.exceptions import PromoCodeValidationError
from promotions.services import PromoCodeService

User = get_user_model()


@pytest.mark.django_db
def test_validate_and_calculate_discount_applies_promo():
    user = User.objects.create_user(username="buyer", password="pass")
    product = Product.objects.create(
        name="T-shirt",
        price=Decimal("100.00"),
        category="clothes",
    )
    promo = PromoCode.objects.create(
        code="SUMMER2025",
        discount_percent=10,
        max_usages=5,
        valid_until=timezone.now() + timedelta(days=1),
        allowed_categories=["clothes"],
    )

    result = PromoCodeService.validate_and_calculate_discount(
        promo_code_str=promo.code,
        user=user,
        items_data=[{"good": product, "quantity": 2}],
    )

    assert result["price"] == Decimal("200.00")
    assert result["discount"] == Decimal("0.10")
    assert result["total"] == Decimal("180.00")
    assert result["calculated_items"][0]["total"] == Decimal("180.00")


@pytest.mark.django_db
def test_validate_rejects_expired_promo():
    user = User.objects.create_user(username="buyer2", password="pass")
    product = Product.objects.create(
        name="Book",
        price=Decimal("50.00"),
        category="books",
    )
    promo = PromoCode.objects.create(
        code="OLD2020",
        discount_percent=10,
        max_usages=5,
        valid_until=timezone.now() - timedelta(days=1),
    )

    with pytest.raises(PromoCodeValidationError):
        PromoCodeService.validate_and_calculate_discount(
            promo_code_str=promo.code,
            user=user,
            items_data=[{"good": product, "quantity": 1}],
        )


@pytest.mark.django_db
def test_validate_rejects_duplicate_user_usage():
    user = User.objects.create_user(username="buyer3", password="pass")
    product = Product.objects.create(
        name="Mug",
        price=Decimal("20.00"),
        category="home",
    )
    promo = PromoCode.objects.create(
        code="ONCE",
        discount_percent=10,
        max_usages=5,
        valid_until=timezone.now() + timedelta(days=1),
    )
    UserPromoUsage.objects.create(user=user, promocode=promo)

    with pytest.raises(PromoCodeValidationError):
        PromoCodeService.validate_and_calculate_discount(
            promo_code_str=promo.code,
            user=user,
            items_data=[{"good": product, "quantity": 1}],
        )


@pytest.mark.django_db
def test_validate_rejects_when_promo_not_applicable_to_any_item():
    user = User.objects.create_user(username="buyer4", password="pass")
    excluded_product = Product.objects.create(
        name="Book",
        price=Decimal("50.00"),
        category="books",
        is_excluded_from_promotions=True,
    )
    PromoCode.objects.create(
        code="ALL20",
        discount_percent=20,
        max_usages=5,
        valid_until=timezone.now() + timedelta(days=1),
    )

    with pytest.raises(PromoCodeValidationError):
        PromoCodeService.validate_and_calculate_discount(
            promo_code_str="ALL20",
            user=user,
            items_data=[{"good": excluded_product, "quantity": 1}],
        )


@pytest.mark.django_db
def test_validate_applies_partial_discount_for_mixed_cart():
    user = User.objects.create_user(username="buyer5", password="pass")
    shirt = Product.objects.create(
        name="Shirt",
        price=Decimal("100.00"),
        category="clothes",
    )
    excluded_book = Product.objects.create(
        name="Book",
        price=Decimal("50.00"),
        category="books",
        is_excluded_from_promotions=True,
    )
    PromoCode.objects.create(
        code="ALL20",
        discount_percent=20,
        max_usages=5,
        valid_until=timezone.now() + timedelta(days=1),
    )

    result = PromoCodeService.validate_and_calculate_discount(
        promo_code_str="ALL20",
        user=user,
        items_data=[
            {"good": shirt, "quantity": 1},
            {"good": excluded_book, "quantity": 1},
        ],
    )

    assert result["price"] == Decimal("150.00")
    assert result["total"] == Decimal("130.00")
    assert result["calculated_items"][0]["discount"] == Decimal("0.20")
    assert result["calculated_items"][0]["total"] == Decimal("80.00")
    assert result["calculated_items"][1]["discount"] == Decimal("0.00")
    assert result["calculated_items"][1]["total"] == Decimal("50.00")
