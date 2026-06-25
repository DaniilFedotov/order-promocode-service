from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class PromoCode(models.Model):
    """Percentage discount code with usage and category rules."""

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_percent = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    max_usages = models.PositiveIntegerField()
    current_usages = models.PositiveIntegerField(default=0)
    valid_until = models.DateTimeField()
    allowed_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Empty list means all categories.",
    )

    class Meta:
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"

    def __str__(self) -> str:
        return f"{self.code} (-{self.discount_percent}%)"


class UserPromoUsage(models.Model):
    """Tracks one promo usage per user."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="used_promos")
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="user_usages")
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "promocode")
        verbose_name = "User Promo Usage"
        verbose_name_plural = "User Promo Usages"
