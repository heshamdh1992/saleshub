from django.core.exceptions import ValidationError
from django.db import transaction

from apps.inventory.models import InventoryTransaction
from apps.products.models import Product


INCREASE_TYPES = {
    InventoryTransaction.TYPE_OPENING,
    InventoryTransaction.TYPE_PURCHASE,
    InventoryTransaction.TYPE_SALE_RETURN,
    InventoryTransaction.TYPE_ADJUSTMENT_ADD,
}

DECREASE_TYPES = {
    InventoryTransaction.TYPE_SALE,
    InventoryTransaction.TYPE_ADJUSTMENT_REMOVE,
    InventoryTransaction.TYPE_DAMAGE,
}


@transaction.atomic
def create_inventory_transaction(
    *,
    merchant,
    product,
    transaction_type,
    quantity,
    user=None,
    note="",
    reference_sale=None,
    reference_number="",
):
    quantity = int(quantity)

    if quantity <= 0:
        raise ValidationError("الكمية يجب أن تكون أكبر من صفر.")

    product = Product.objects.select_for_update().get(pk=product.pk, merchant=merchant)
    balance_before = int(product.stock_quantity)

    if transaction_type in INCREASE_TYPES:
        balance_after = balance_before + quantity
    elif transaction_type in DECREASE_TYPES:
        balance_after = balance_before - quantity
        if balance_after < 0:
            raise ValidationError(
                f"المخزون غير كافٍ للمنتج '{product.name}'. المتاح: {balance_before}"
            )
    else:
        raise ValidationError("نوع حركة المخزون غير صالح.")

    tx = InventoryTransaction.objects.create(
        merchant=merchant,
        product=product,
        transaction_type=transaction_type,
        quantity=quantity,
        balance_before=balance_before,
        balance_after=balance_after,
        reference_sale=reference_sale,
        reference_number=reference_number,
        note=note,
        created_by=user,
    )

    product.stock_quantity = balance_after
    product.save(update_fields=["stock_quantity"])

    return tx


@transaction.atomic
def create_sale_inventory_transactions(*, sale, user=None):
    existing = InventoryTransaction.objects.filter(
        merchant=sale.merchant,
        reference_sale=sale,
        transaction_type=InventoryTransaction.TYPE_SALE,
    ).exists()

    if existing:
        return []

    created = []

    for item in sale.items.select_related("product").all():
        tx = create_inventory_transaction(
            merchant=sale.merchant,
            product=item.product,
            transaction_type=InventoryTransaction.TYPE_SALE,
            quantity=item.quantity,
            user=user,
            note=f"Sale {sale.invoice_number}",
            reference_sale=sale,
            reference_number=sale.invoice_number or "",
        )
        created.append(tx)

    return created