from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

API_V1_PREFIX = "api/v1/"
SCHEMA_URL = "api/schema/"
DOCS_URL = "api/docs/"

urlpatterns = [
    path(API_V1_PREFIX, include("orders.urls", namespace="orders-v1")),
    path(SCHEMA_URL, SpectacularAPIView.as_view(), name="schema"),
    path(DOCS_URL, SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
