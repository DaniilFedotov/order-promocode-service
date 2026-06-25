from decimal import Decimal

from promotions.types import CalculatedLineItem, OrderCalculationResult, OrderLineInput


def calculate_order_without_promo(items: list[OrderLineInput]) -> OrderCalculationResult:
    """Build order totals when no promo code is supplied."""
    calculated_items: list[CalculatedLineItem] = []
    total_price = Decimal("0.00")

    for item in items:
        line_total = item["good"].price * item["quantity"]
        total_price += line_total
        calculated_items.append(
            {
                "good": item["good"],
                "quantity": item["quantity"],
                "price": item["good"].price,
                "discount": Decimal("0.00"),
                "total": line_total,
            }
        )

    return {
        "promo_code_obj": None,
        "calculated_items": calculated_items,
        "price": total_price,
        "discount": Decimal("0.00"),
        "total": total_price,
    }
