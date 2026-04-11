from django.urls import path
from .views import InventoryAlertsView

app_name = "inventory"

urlpatterns = [
    path("alerts/", InventoryAlertsView.as_view(), name="alerts"),
]