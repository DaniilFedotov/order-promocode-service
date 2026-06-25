from decimal import Decimal
from typing import TypedDict

from orders.models import Product
from promotions.models import PromoCode


class OrderLineInput(TypedDict):
    """Single cart line passed into promo calculation."""

    good: Product
    quantity: int


class CalculatedLineItem(TypedDict):
    """Calculated values for one order line."""

    good: Product
    quantity: int
    price: Decimal
    discount: Decimal
    total: Decimal


class OrderCalculationResult(TypedDict):
    """Pricing result used when persisting an order."""

    promo_code_obj: PromoCode | None
    calculated_items: list[CalculatedLineItem]
    price: Decimal
    discount: Decimal
    total: Decimal
