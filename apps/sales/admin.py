from django.contrib import admin
from .models import Sale, SaleItem, Payment


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "merchant", "customer", "payment_type", "payment_status", "total_amount", "amount_due", "created_at")
    list_filter = ("merchant", "payment_type", "payment_status")
    search_fields = ("invoice_number", "customer__name")
    inlines = [SaleItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("sale", "customer", "amount", "created_at")
    search_fields = ("sale__invoice_number", "customer__name")