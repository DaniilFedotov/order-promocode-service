from decimal import Decimal

PERCENT_BASE = Decimal("100")

PROMO_CODE_NOT_FOUND = "The promo code does not exist."
PROMO_CODE_EXPIRED = "This promo code has expired."
PROMO_CODE_USAGE_LIMIT = "This promo code has reached its maximum usage limit."
PROMO_CODE_ALREADY_USED = "You have already used this promo code once."
PROMO_CODE_NOT_APPLICABLE = "The promo code is valid but cannot be applied to any items."
PROMO_CODE_CONCURRENT_USAGE = "Promo usage threshold was just breached by a parallel checkout."
