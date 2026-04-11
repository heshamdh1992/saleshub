from decimal import Decimal
from django.db import models
from django.db.models import Sum
from apps.core.models import TimeStampedModel


class Customer(TimeStampedModel):
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.CASCADE,
        related_name="customers"
    )
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        constraints = [
            models.UniqueConstraint(
                fields=["merchant", "phone"],
                name="unique_phone_per_merchant",
                condition=models.Q(phone__gt="")
            )
        ]

    def __str__(self):
        return self.name

    def total_invoices_amount(self):
        return self.sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")

    def total_payments_amount(self):
        return self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    def balance(self):
        return self.total_invoices_amount() - self.total_payments_amount()