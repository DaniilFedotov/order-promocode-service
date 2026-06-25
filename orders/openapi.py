from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from drf_spectacular.types import OpenApiTypes
from rest_framework import status

from orders.serializers import OrderCreateSerializer
from promotions.constants import PROMO_CODE_EXPIRED, PROMO_CODE_NOT_APPLICABLE

ORDER_CREATE_REQUEST_EXAMPLE = OpenApiExample(
    "Order with promo",
    value={
        "user_id": 1,
        "goods": [{"good_id": 1, "quantity": 2}],
        "promo_code": "SUMMER2025",
    },
    request_only=True,
)

PROMO_EXPIRED_RESPONSE_EXAMPLE = OpenApiExample(
    "Expired promo code",
    value={"promo_code": [PROMO_CODE_EXPIRED]},
    response_only=True,
    status_codes=["400"],
)

PROMO_NOT_APPLICABLE_RESPONSE_EXAMPLE = OpenApiExample(
    "Promo not applicable to any items",
    value={"promo_code": [PROMO_CODE_NOT_APPLICABLE]},
    response_only=True,
    status_codes=["400"],
)

order_create_schema = extend_schema(
    request=OrderCreateSerializer,
    responses={
        status.HTTP_201_CREATED: OrderCreateSerializer,
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Validation error (promo rules or request payload).",
            examples=[PROMO_EXPIRED_RESPONSE_EXAMPLE, PROMO_NOT_APPLICABLE_RESPONSE_EXAMPLE],
        ),
    },
    examples=[ORDER_CREATE_REQUEST_EXAMPLE],
)
