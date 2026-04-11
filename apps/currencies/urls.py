from django.urls import path
from .views import (
    CurrencyListView,
    CurrencyCreateView,
    CurrencyUpdateView,
    ExchangeRateListView,
    ExchangeRateCreateView,
    ExchangeRateUpdateView,
    ExchangeRateActivateView,
)

app_name = "currencies"

urlpatterns = [
    path("", CurrencyListView.as_view(), name="currency_list"),
    path("add/", CurrencyCreateView.as_view(), name="currency_add"),
    path("<int:pk>/edit/", CurrencyUpdateView.as_view(), name="currency_edit"),

    path("rates/", ExchangeRateListView.as_view(), name="rate_list"),
    path("rates/add/", ExchangeRateCreateView.as_view(), name="rate_add"),
    path("rates/<int:pk>/edit/", ExchangeRateUpdateView.as_view(), name="rate_edit"),
    path("rates/<int:pk>/activate/", ExchangeRateActivateView.as_view(), name="rate_activate"),
]