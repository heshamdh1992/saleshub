from django.db import models
from apps.core.models import TimeStampedModel


class Currency(TimeStampedModel):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class ExchangeRate(TimeStampedModel):
    base_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="base_exchange_rates"
    )
    quote_currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="quote_exchange_rates"
    )
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["base_currency", "quote_currency", "is_active"],
                name="unique_active_exchange_rate_pair"
            )
        ]

    def __str__(self):
        return f"1 {self.base_currency.code} = {self.rate} {self.quote_currency.code}"