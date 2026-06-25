from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.openapi import order_create_schema
from orders.serializers import OrderCreateSerializer


@order_create_schema
class OrderCreateAPIView(APIView):
    """Create an order with optional promo code."""

    serializer_class = OrderCreateSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
