from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.core.mixins import MerchantRequiredMixin
from apps.products.models import Product
from django.db import models


class InventoryAlertsView(LoginRequiredMixin, MerchantRequiredMixin, TemplateView):
    template_name = "inventory/alerts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        merchant = self.get_merchant()

        out_of_stock_products = Product.objects.filter(
            merchant=merchant,
            is_active=True,
            stock_quantity__lte=0
        ).order_by("name")

        low_stock_products = Product.objects.filter(
            merchant=merchant,
            is_active=True,
            stock_quantity__gt=0,
            stock_quantity__lte=models.F("reorder_level")
        ).order_by("stock_quantity", "name")

        context.update({
            "out_of_stock_products": out_of_stock_products,
            "low_stock_products": low_stock_products,
            "out_of_stock_count": out_of_stock_products.count(),
            "low_stock_count": low_stock_products.count(),
        })
        return context