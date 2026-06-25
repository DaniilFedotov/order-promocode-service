from django.urls import path

from orders.views import OrderCreateAPIView

app_name = "orders"

urlpatterns = [
    path(
        "orders/",
        OrderCreateAPIView.as_view(),
        name="order-create"
    ),
]
