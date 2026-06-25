from django.contrib.auth import get_user_model
from django.db import models

from promotions.models import PromoCode

User = get_user_model()


class Product(models.Model):
    """Purchasable product."""

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, db_index=True)
    is_excluded_from_promotions = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Good"
        verbose_name_plural = "Goods"

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    """Customer order with optional promo code."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    promo_code_obj = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    """Single line inside an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    good = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
