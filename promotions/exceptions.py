from rest_framework.exceptions import ValidationError


class PromoCodeValidationError(ValidationError):
    """Raised when a promo code fails business validation."""
