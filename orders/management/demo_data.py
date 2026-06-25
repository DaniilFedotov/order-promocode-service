from decimal import Decimal
from typing import TypedDict


class DemoProduct(TypedDict):
    """Seed product definition."""

    id: int
    name: str
    price: Decimal
    category: str
    is_excluded_from_promotions: bool


class DemoPromo(TypedDict):
    """Seed promo code definition."""

    code: str
    discount_percent: int
    max_usages: int
    valid_for_days: int
    allowed_categories: list[str]


DEMO_USERS: list[tuple[int, str]] = [
    (1, "demo_user_1"),
    (2, "demo_user_2"),
    (3, "demo_user_3"),
    (4, "demo_user_4"),
    (5, "demo_user_5"),
]

DEMO_PRODUCTS: list[DemoProduct] = [
    {
        "id": 1,
        "name": "T-shirt",
        "price": Decimal("100.00"),
        "category": "clothes",
        "is_excluded_from_promotions": False,
    },
    {
        "id": 2,
        "name": "Book",
        "price": Decimal("50.00"),
        "category": "books",
        "is_excluded_from_promotions": True,
    },
    {
        "id": 3,
        "name": "Notebook",
        "price": Decimal("30.00"),
        "category": "stationery",
        "is_excluded_from_promotions": False,
    },
]

DEMO_PROMOS: list[DemoPromo] = [
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
