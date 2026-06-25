from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from orders.models import Product
from promotions.models import PromoCode

User = get_user_model()


@pytest.fixture
def api_client():
    """Return a DRF API client."""
    return APIClient()


@pytest.mark.django_db
def test_create_order_without_promo(api_client):
    user = User.objects.create_user(username="client", password="pass")
    product = Product.objects.create(
        name="Notebook",
        price=Decimal("100.00"),
        category="office",
    )
    url = reverse("orders-v1:order-create")

    response = api_client.post(
        url,
        {
            "user_id": user.id,
            "goods": [{"good_id": product.id, "quantity": 2}],
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data == {
        "user_id": user.id,
        "order_id": response.data["order_id"],
        "goods": [
            {
                "good_id": product.id,
                "quantity": 2,
                "price": "100.00",
                "discount": "0.00",
                "total": "200.00",
            }
        ],
        "price": "200.00",
        "discount": "0.00",
        "total": "200.00",
    }


@pytest.mark.django_db
def test_create_order_with_promo(api_client):
    user = User.objects.create_user(username="client2", password="pass")
    product = Product.objects.create(
        name="Shirt",
        price=Decimal("100.00"),
        category="clothes",
    )
    PromoCode.objects.create(
        code="SUMMER2025",
        discount_percent=10,
        max_usages=5,
        valid_until=timezone.now() + timedelta(days=1),
        allowed_categories=["clothes"],
    )
    url = reverse("orders-v1:order-create")

    response = api_client.post(
        url,
        {
            "user_id": user.id,
            "goods": [{"good_id": product.id, "quantity": 2}],
            "promo_code": "SUMMER2025",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["price"] == "200.00"
    assert response.data["discount"] == "0.10"
    assert response.data["total"] == "180.00"
    assert response.data["goods"][0]["total"] == "180.00"


@pytest.mark.django_db
def test_create_order_rejects_promo_when_not_applicable_to_any_item(api_client):
    user = User.objects.create_user(username="client3", password="pass")
    product = Product.objects.create(
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
    url = reverse("orders-v1:order-create")

    response = api_client.post(
        url,
        {
            "user_id": user.id,
            "goods": [{"good_id": product.id, "quantity": 1}],
            "promo_code": "ALL20",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "promo_code" in response.data


@pytest.mark.django_db
def test_create_order_applies_partial_promo_for_mixed_cart(api_client):
    user = User.objects.create_user(username="client4", password="pass")
    shirt = Product.objects.create(
        name="Shirt",
        price=Decimal("100.00"),
        category="clothes",
    )
    book = Product.objects.create(
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
    url = reverse("orders-v1:order-create")

    response = api_client.post(
        url,
        {
            "user_id": user.id,
            "goods": [
                {"good_id": shirt.id, "quantity": 1},
                {"good_id": book.id, "quantity": 1},
            ],
            "promo_code": "ALL20",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["price"] == "150.00"
    assert response.data["total"] == "130.00"
    assert response.data["goods"][0]["discount"] == "0.20"
    assert response.data["goods"][0]["total"] == "80.00"
    assert response.data["goods"][1]["discount"] == "0.00"
    assert response.data["goods"][1]["total"] == "50.00"
