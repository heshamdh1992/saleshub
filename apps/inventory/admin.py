from django.contrib import admin
from .models import InventoryTransaction


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("product", "transaction_type", "quantity", "merchant", "created_at")
    list_filter = ("merchant", "transaction_type")
    search_fields = ("product__name", "note")