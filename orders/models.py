from django.db import models
from django.contrib.auth import get_user_model

from promotions.models import PromoCode

User = get_user_model()


class Product(models.Model):
    """
    Represents a purchasable store item bound to a category, supporting campaign exclusions.
    """
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, db_index=True)
    is_excluded_from_promotions = models.BooleanField(
        default=False,
        help_text="If True, promo codes will completely skip this product during calculations."
    )

    class Meta:
        verbose_name = "Good"
        verbose_name_plural = "Goods"

    def __str__(self):
        return self.name


class Order(models.Model):
    """
    Main order ledger that persists the client user, the used coupon,
    and total amounts before and after promotional deductions.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    promo_code_obj = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total price before discount.")
    discount = models.DecimalField(max_digits=4, decimal_places=2, default=0.00,
                                   help_text="Applied discount fraction (e.g. 0.1).")
    total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Final price paid after discount.")

    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    """
    A line item inside an order capturing specific product quantities and historical unit prices.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    good = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Historical unit price.")
    discount = models.DecimalField(max_digits=4, decimal_places=2, default=0.00,
                                   help_text="Item level discount fraction.")
    total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Calculated line item cost.")
