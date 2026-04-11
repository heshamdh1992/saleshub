from django.utils import timezone
from .models import Sale


def generate_invoice_number():
    year = timezone.now().year
    prefix = f"INV-{year}-"
    last_sale = (
        Sale.objects.filter(invoice_number__startswith=prefix)
        .order_by("-invoice_number")
        .first()
    )

    if not last_sale:
        return f"{prefix}000001"

    last_number = int(last_sale.invoice_number.replace(prefix, ""))
    return f"{prefix}{last_number + 1:06d}"