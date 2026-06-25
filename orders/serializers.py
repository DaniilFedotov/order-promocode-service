from decimal import Decimal

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction

from orders.models import Product, Order, OrderItem
from promotions.services import PromoCodeService

User = get_user_model()


class OrderItemResponseSerializer(serializers.ModelSerializer):
    """
    Item nested structure inside the response body.
    """
    good_id = serializers.IntegerField(source="good.id")

    class Meta:
        model = OrderItem
        fields = ["good_id", "quantity", "price", "discount", "total"]


class OrderItemPostSerializer(serializers.Serializer):
    """
    Validates individual item structures inside the incoming basket payload.
    """
    good_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate_good_id(self, value):
        """
        Ensures the requested product actually exists in the database.
        """
        try:
            return Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Requested product does not exist.")


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Handles request validation and database orchestration for order checkouts.
    """
    user_id = serializers.IntegerField()
    goods = OrderItemPostSerializer(many=True, write_only=True)
    promo_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)

    # Remap model outputs into client contract fields using serializermethods/source fields
    order_id = serializers.IntegerField(source="id", read_only=True)
    response_goods = OrderItemResponseSerializer(many=True, source="items", read_only=True)

    class Meta:
        model = Order
        fields = ["user_id", "order_id", "goods", "promo_code", "response_goods", "price", "discount", "total"]
        read_only_fields = ["order_id", "response_goods", "price", "discount", "total"]

    def validate_user_id(self, value):
        try:
            return User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

    def validate(self, attrs):
        """
        Transforms product IDs into object references and executes the PromoCodeService
        to calculate raw and discounted totals before saving.
        """
        user = attrs["user_id"]
        raw_goods = attrs.get("goods", [])
        promo_code_str = attrs.get("promo_code")

        prepared_items = [
            {"good": item["good_id"], "quantity": item["quantity"]}
            for item in raw_goods
        ]

        if promo_code_str:
            calc_result = PromoCodeService.validate_and_calculate_discount(
                promo_code_str=promo_code_str,
                user=user,
                items_data=prepared_items
            )
            attrs["_calc_data"] = calc_result
        else:
            # Fallback path if no promo code supplied
            calculated_items = []
            total_price = Decimal("0.00")
            for item in prepared_items:
                line_total = item["good"].price * item["quantity"]
                total_price += line_total
                calculated_items.append({
                    "good": item["good"],
                    "quantity": item["quantity"],
                    "price": item["good"].price,
                    "discount": Decimal("0.00"),
                    "total": line_total
                })
            attrs["_calc_data"] = {
                "promo_code_obj": None,
                "calculated_items": calculated_items,
                "price": total_price,
                "discount": Decimal("0.00"),
                "total": total_price
            }

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """
        Persists the order ledger tables and commits promo utilization inside a single transaction.
        """
        calc_data = validated_data["_calc_data"]

        order = Order.objects.create(
            user=validated_data["user_id"],
            promo_code_obj=calc_data["promo_code_obj"],
            price=calc_data["price"],
            discount=calc_data["discount"],
            total=calc_data["total"]
        )

        order_items = [
            OrderItem(
                order=order,
                good=item["good"],
                quantity=item["quantity"],
                price=item["price"],
                discount=item["discount"],
                total=item["total"]
            )
            for item in calc_data["calculated_items"]
        ]
        OrderItem.objects.bulk_create(order_items)

        if calc_data["promo_code_obj"]:
            PromoCodeService.register_usage(promocode=calc_data["promo_code_obj"], user=validated_data["user_id"])

        return order


    def to_representation(self, instance):
        """
        Reorder properties dynamically to precisely simulate the assignment requirements output sequence.
        """
        repr_data = super().to_representation(instance)
        return {
            "user_id": repr_data["user_id"],
            "order_id": repr_data["order_id"],
            "goods": repr_data["response_goods"],
            "price": repr_data["price"],
            "discount": repr_data["discount"],
            "total": repr_data["total"]
        }