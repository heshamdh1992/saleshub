from django.db import models
from apps.core.models import TimeStampedModel


class InventoryTransaction(TimeStampedModel):
    TRANSACTION_TYPE_CHOICES = [
        ("sale", "Sale"),
        ("adjustment_add", "Adjustment Add"),
        ("adjustment_remove", "Adjustment Remove"),
    ]

    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.CASCADE,
        related_name="inventory_transactions"
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="inventory_transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.IntegerField()
    reference_sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_transactions"
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def str(self):
        return f"{self.product.name} - {self.transaction_type} - {self.quantity}"