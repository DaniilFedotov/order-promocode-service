from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from orders.serializers import OrderCreateSerializer


class OrderCreateAPIView(APIView):
    """
    HTTP POST Endpoint to securely process cart items, validate promotional campaigns,
    and create client system orders.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Receives order items payload and coupon strings, processing checkout pipelines.
        """
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            order = serializer.save()
            # Return serialized order data along with HTTP 201 Created status
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
