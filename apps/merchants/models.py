from django.db import models
from apps.core.models import TimeStampedModel


class Merchant(TimeStampedModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to="merchant_logos/", blank=True, null=True)
    invoice_note = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Merchant"
        verbose_name_plural = "Merchants"

    def __str__(self):
        return self.name