from decimal import Decimal

from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError

from promotions.models import PromoCode, UserPromoUsage


class PromoCodeValidationError(ValidationError):
    """Custom API exception specialized for descriptive promotion validation issues."""
    pass


class PromoCodeService:
    """
    Domain service isolating the core business rules for promo validation and calculations.
    """

    @classmethod
    def validate_and_calculate_discount(cls, promo_code_str: str, user, items_data: list) -> dict:
        """
        Validates a promotional coupon against 6 core criteria and calculates final costs.

        Expected items_data format: [{'product': Product, 'quantity': int}, ...]
        Returns a dict with: 'promocode', 'total_amount_raw', 'total_amount_discounted'
        """
        # Rule 1: The promo code must exist in the database
        try:
            promocode = PromoCode.objects.get(code=promo_code_str)
        except PromoCode.DoesNotExist:
            raise PromoCodeValidationError({"promocode": "The promo code does not exist."})

        # Rule 2: The promo code must not be expired
        if promocode.valid_until < timezone.now():
            raise PromoCodeValidationError({"promocode": "This promo code has expired."})

        # Rule 3: The promo code must not exceed its global total usage limit
        if promocode.current_usages >= promocode.max_usages:
            raise PromoCodeValidationError({"promocode": "This promo code has reached its maximum usage limit."})

        # Rule 4: A single user cannot use the same promo code more than once
        if UserPromoUsage.objects.filter(user=user, promocode=promocode).exists():
            raise PromoCodeValidationError({"promocode": "You have already used this promo code once."})

        calculated_items = []
        total_price = Decimal("0.00")
        total_discounted = Decimal("0.00")
        is_promo_applied_at_least_once = False

        for item in items_data:
            good = item["good"]
            quantity = item["quantity"]
            line_raw_price = good.price * quantity
            total_price += line_raw_price

            item_discount_fraction = Decimal("0.00")

            # Apply rules 5 & 6
            if not good.is_excluded_from_promotions:
                if not promocode.allowed_categories or good.category in promocode.allowed_categories:
                    item_discount_fraction = Decimal(promocode.discount_percent) / Decimal("100.00")
                    is_promo_applied_at_least_once = True

            line_discount_amount = line_raw_price * item_discount_fraction
            line_final_total = line_raw_price - line_discount_amount
            total_discounted += line_final_total

            calculated_items.append({
                "good": good,
                "quantity": quantity,
                "price": good.price,
                "discount": item_discount_fraction,
                "total": line_final_total
            })

        if not is_promo_applied_at_least_once:
            raise PromoCodeValidationError(
                {"promo_code": "The promo code is valid but cannot be applied to any items."})

        # Global aggregate discount percentage representation
        global_discount_fraction = Decimal(promocode.discount_percent) / Decimal("100.00")

        return {
            "promo_code_obj": promocode,
            "calculated_items": calculated_items,
            "price": total_price,
            "discount": global_discount_fraction,
            "total": total_discounted
        }

    @classmethod
    @transaction.atomic
    def register_usage(cls, promocode: PromoCode, user) -> None:
        """
        Locks the row using select_for_update to avoid concurrent transaction race conditions,
        verifies remaining slots, increments the global count, and logs user utilization.
        """
        # Lock the row to prevent over-allocation during concurrent requests
        locked_promocode = PromoCode.objects.select_for_update().get(pk=promocode.pk)

        if locked_promocode.current_usages >= locked_promocode.max_usages:
            raise PromoCodeValidationError(
                {"promocode": "Promo usage threshold was just breached by a parallel checkout."})

        # Log the immutable fact of single user coupon utilization
        UserPromoUsage.objects.create(user=user, promocode=locked_promocode)

        # Safely persist incremented counters back to the DB layer
        locked_promocode.current_usages += 1
        locked_promocode.save()
