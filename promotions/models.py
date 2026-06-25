from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class PromoCode(models.Model):
    """
    Represents a promotional code that grants a percentage discount
    on orders based on specific conditional rules.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique alphanumeric code entered by the user."
    )
    discount_percent = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Percentage discount value from 1 to 100."
    )
    max_usages = models.PositiveIntegerField(
        help_text="Global maximum number of times this promo code can be used."
    )
    current_usages = models.PositiveIntegerField(
        default=0,
        help_text="Tracks how many times this promo code has been successfully applied."
    )
    valid_until = models.DateTimeField(
        help_text="The expiration date and time of the promotional campaign."
    )
    allowed_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="List of product category slugs this promo applies to. If empty, applies to all."
    )

    class Meta:
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"


class UserPromoUsage(models.Model):
    """
    Tracks historical usages of promotional codes by individual users
     to guarantee a strict 'once-per-user' policy constraint.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="used_promos")
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="user_usages")
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Enforces Rule 4: One user cannot use the same promo code more than once
        unique_together = ("user", "promocode")
        verbose_name = "User Promo Usage"
        verbose_name_plural = "User Promo Usages"
