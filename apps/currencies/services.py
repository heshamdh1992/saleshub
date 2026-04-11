from decimal import Decimal
from .models import Currency, ExchangeRate


def get_active_exchange_rate(base_code="USD", quote_code="USD"):
    if base_code == quote_code:
        return Decimal("1.000000")

    base_currency = Currency.objects.filter(code=base_code, is_active=True).first()
    quote_currency = Currency.objects.filter(code=quote_code, is_active=True).first()

    if not base_currency or not quote_currency:
        raise ValueError(f"Currency not found or inactive: {base_code} -> {quote_code}")

    rate = ExchangeRate.objects.filter(
        base_currency=base_currency,
        quote_currency=quote_currency,
        is_active=True
    ).order_by("-created_at").first()

    if not rate:
        raise ValueError(f"No active exchange rate found for {base_code} -> {quote_code}")

    return rate.rate