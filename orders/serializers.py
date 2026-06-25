from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from rest_framework import serializers

from orders.models import Order, OrderItem, Product
from orders.services import calculate_order_without_promo
from promotions.exceptions import PromoCodeValidationError
from promotions.services import PromoCodeService
from promotions.types import OrderLineInput

User = get_user_model()


class OrderItemResponseSerializer(serializers.ModelSerializer):
    """Order line item in API response."""

    good_id = serializers.IntegerField(source="good.id")

    class Meta:
        model = OrderItem
        fields = ["good_id", "quantity", "price", "discount", "total"]


class OrderItemPostSerializer(serializers.Serializer):
    """Order line item in API request."""

    good_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_good_id(self, value: int) -> Product:
        try:
            return Product.objects.get(id=value)
        except Product.DoesNotExist as exc:
            raise serializers.ValidationError("Requested product does not exist.") from exc


class OrderCreateSerializer(serializers.ModelSerializer):
    """Validate and create an order."""

    user_id = serializers.IntegerField()
    goods = OrderItemPostSerializer(many=True, write_only=True)
    promo_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    order_id = serializers.IntegerField(source="id", read_only=True)
    response_goods = OrderItemResponseSerializer(many=True, source="items", read_only=True)

    class Meta:
        model = Order
        fields = ["user_id", "order_id", "goods", "promo_code", "response_goods", "price", "discount", "total"]
        read_only_fields = ["order_id", "response_goods", "price", "discount", "total"]

    def validate_user_id(self, value: int) -> AbstractBaseUser:
        try:
            return User.objects.get(id=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("User does not exist.") from exc

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = attrs["user_id"]
        prepared_items: list[OrderLineInput] = [
            {"good": item["good_id"], "quantity": item["quantity"]}
            for item in attrs.get("goods", [])
        ]
        promo_code = attrs.get("promo_code")

        if promo_code:
            try:
                attrs["_calc_data"] = PromoCodeService.validate_and_calculate_discount(
                    promo_code_str=promo_code,
                    user=user,
                    items_data=prepared_items,
                )
            except PromoCodeValidationError as exc:
                raise serializers.ValidationError(exc.detail) from exc
        else:
            attrs["_calc_data"] = calculate_order_without_promo(prepared_items)

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Order:
        calc_data = validated_data["_calc_data"]
        user = validated_data["user_id"]

        order = Order.objects.create(
            user=user,
            promo_code_obj=calc_data["promo_code_obj"],
            price=calc_data["price"],
            discount=calc_data["discount"],
            total=calc_data["total"],
        )

        OrderItem.objects.bulk_create(
            [
                OrderItem(
                    order=order,
                    good=item["good"],
                    quantity=item["quantity"],
                    price=item["price"],
                    discount=item["discount"],
                    total=item["total"],
                )
                for item in calc_data["calculated_items"]
            ]
        )

        if calc_data["promo_code_obj"]:
            PromoCodeService.register_usage(promocode=calc_data["promo_code_obj"], user=user)

        return order

    def to_representation(self, instance: Order) -> dict[str, Any]:
        data = super().to_representation(instance)
        return {
            "user_id": instance.user_id,
            "order_id": data["order_id"],
            "goods": data["response_goods"],
            "price": data["price"],
            "discount": data["discount"],
            "total": data["total"],
        }
