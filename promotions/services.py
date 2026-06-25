from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils import timezone

from orders.models import Product
from promotions.constants import (
    PERCENT_BASE,
    PROMO_CODE_ALREADY_USED,
    PROMO_CODE_CONCURRENT_USAGE,
    PROMO_CODE_EXPIRED,
    PROMO_CODE_NOT_APPLICABLE,
    PROMO_CODE_NOT_FOUND,
    PROMO_CODE_USAGE_LIMIT,
)
from promotions.exceptions import PromoCodeValidationError
from promotions.models import PromoCode, UserPromoUsage
from promotions.types import CalculatedLineItem, OrderCalculationResult, OrderLineInput


class PromoCodeService:
    """Promo code validation and order pricing."""

    @classmethod
    def validate_and_calculate_discount(
        cls,
        promo_code_str: str,
        user: AbstractBaseUser,
        items_data: list[OrderLineInput],
    ) -> OrderCalculationResult:
        """Validate promo rules and return calculated order totals."""
        promocode = cls._get_active_promo(promo_code_str)
        cls._ensure_user_has_not_used_promo(user, promocode)

        calculated_items: list[CalculatedLineItem] = []
        total_price = Decimal("0.00")
        total_discounted = Decimal("0.00")
        is_promo_applied = False

        for item in items_data:
            good = item["good"]
            quantity = item["quantity"]
            line_raw_price = good.price * quantity
            total_price += line_raw_price

            item_discount_fraction = Decimal("0.00")
            if cls._is_promo_applicable_to_product(promocode, good):
                item_discount_fraction = Decimal(promocode.discount_percent) / PERCENT_BASE
                is_promo_applied = True

            line_final_total = line_raw_price - (line_raw_price * item_discount_fraction)
            total_discounted += line_final_total
            calculated_items.append(
                {
                    "good": good,
                    "quantity": quantity,
                    "price": good.price,
                    "discount": item_discount_fraction,
                    "total": line_final_total,
                }
            )

        if not is_promo_applied:
            raise PromoCodeValidationError({"promo_code": PROMO_CODE_NOT_APPLICABLE})

        global_discount_fraction = Decimal(promocode.discount_percent) / PERCENT_BASE
        return {
            "promo_code_obj": promocode,
            "calculated_items": calculated_items,
            "price": total_price,
            "discount": global_discount_fraction,
            "total": total_discounted,
        }

    @classmethod
    @transaction.atomic
    def register_usage(cls, promocode: PromoCode, user: AbstractBaseUser) -> None:
        """Record promo usage with row-level locking."""
        locked_promocode = PromoCode.objects.select_for_update().get(pk=promocode.pk)

        if locked_promocode.current_usages >= locked_promocode.max_usages:
            raise PromoCodeValidationError({"promo_code": PROMO_CODE_CONCURRENT_USAGE})

        UserPromoUsage.objects.create(user=user, promocode=locked_promocode)
        locked_promocode.current_usages += 1
        locked_promocode.save(update_fields=["current_usages"])

    @classmethod
    def _get_active_promo(cls, promo_code_str: str) -> PromoCode:
        try:
            promocode = PromoCode.objects.get(code=promo_code_str)
        except PromoCode.DoesNotExist as exc:
            raise PromoCodeValidationError({"promo_code": PROMO_CODE_NOT_FOUND}) from exc

        if promocode.valid_until < timezone.now():
            raise PromoCodeValidationError({"promo_code": PROMO_CODE_EXPIRED})

        if promocode.current_usages >= promocode.max_usages:
            raise PromoCodeValidationError({"promo_code": PROMO_CODE_USAGE_LIMIT})

        return promocode

    @staticmethod
    def _ensure_user_has_not_used_promo(user: AbstractBaseUser, promocode: PromoCode) -> None:
        if UserPromoUsage.objects.filter(user=user, promocode=promocode).exists():
            raise PromoCodeValidationError({"promo_code": PROMO_CODE_ALREADY_USED})

    @staticmethod
    def _is_promo_applicable_to_product(promocode: PromoCode, good: Product) -> bool:
        if good.is_excluded_from_promotions:
            return False
        if promocode.allowed_categories and good.category not in promocode.allowed_categories:
            return False
        return True
