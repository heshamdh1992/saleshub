from django.urls import path
from .views import MerchantDetailView, MerchantUpdateView

app_name = "merchants"

urlpatterns = [
    path("current/", MerchantDetailView.as_view(), name="current"),
    path("current/edit/", MerchantUpdateView.as_view(), name="edit"),
]