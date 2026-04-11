from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "merchant",
        "sku",
        "barcode",
        "base_price_usd",
        "stock_quantity",
        "is_active",
        "created_at",
    )
    list_filter = ("merchant", "is_active")
    search_fields = ("name", "sku", "barcode")