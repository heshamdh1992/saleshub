from django.urls import path
from .views import (
    CustomerListView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDetailView,
)

app_name = "customers"

urlpatterns = [
    path("", CustomerListView.as_view(), name="list"),
    path("add/", CustomerCreateView.as_view(), name="add"),
    path("<int:pk>/", CustomerDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", CustomerUpdateView.as_view(), name="edit"),
]