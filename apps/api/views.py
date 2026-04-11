from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.utils.timezone import now
from apps.core.mixins import CashierOrAboveRequiredMixin
from apps.currencies.models import ExchangeRate
from apps.products.models import Product
import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.views import View

from apps.core.mixins import CashierOrAboveRequiredMixin
from apps.currencies.models import Currency
from apps.inventory.models import InventoryTransaction
from apps.products.models import Product
from apps.sales.models import Sale, SaleItem, Payment
from apps.sales.models import Sale, SaleItem, Payment, generate_invoice_number

class OfflineBootstrapView(LoginRequiredMixin, CashierOrAboveRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        merchant = self.get_merchant()

        products = Product.objects.filter(
            merchant=merchant,
            is_active=True
        ).order_by("name")

        product_data = []
        for product in products:
            product_data.append({
                "id": product.id,
                "name": product.name,
                "sku": product.sku or "",
                "barcode": product.barcode or "",
                "base_price_usd": str(product.base_price_usd),
                "cost_price_usd": str(product.cost_price_usd),
                "stock_quantity": product.stock_quantity,
                "reorder_level": product.reorder_level,
                "stock_status": product.stock_status,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
            })

        exchange_rates = ExchangeRate.objects.filter(
            is_active=True
        ).select_related("base_currency", "quote_currency").order_by(
            "base_currency__code", "quote_currency__code"
        )

        exchange_rate_data = []
        for rate in exchange_rates:
            exchange_rate_data.append({
                "id": rate.id,
                "base_currency": rate.base_currency.code,
                "quote_currency": rate.quote_currency.code,
                "rate": str(rate.rate),
                "updated_at": rate.updated_at.isoformat() if rate.updated_at else None,
            })

        merchant_data = {
            "id": merchant.id,
            "name": merchant.name,
            "phone": merchant.phone or "",
            "address": merchant.address or "",
            "invoice_note": merchant.invoice_note or "",
            "logo_url": merchant.logo.url if merchant.logo else "",
        }

        payload = {
            "ok": True,
            "merchant": merchant_data,
            "products": product_data,
            "exchange_rates": exchange_rate_data,
            "generated_at": now().isoformat(),
            "counts": {
                "products": len(product_data),
                "exchange_rates": len(exchange_rate_data),
            }
        }

        return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})
    
class OfflineSyncSalesView(LoginRequiredMixin, CashierOrAboveRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        merchant = self.get_merchant()

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({
                "ok": False,
                "message": "البيانات المرسلة غير صالحة."
            }, status=400)

        sales = payload.get("sales", [])
        if not isinstance(sales, list) or not sales:
            return JsonResponse({
                "ok": False,
                "message": "لا توجد عمليات بيع للمزامنة."
            }, status=400)

        results = []

        for sale_data in sales:
            offline_id = sale_data.get("offline_id")
            if not offline_id:
                results.append({
                    "offline_id": None,
                    "ok": False,
                    "message": "offline_id مفقود."
                })
                continue

            existing_sale = Sale.objects.filter(
                merchant=merchant,
                offline_id=offline_id
            ).first()

            if existing_sale:
                results.append({
                    "offline_id": offline_id,
                    "ok": True,
                    "status": "already_synced",
                    "sale_id": existing_sale.id,
                    "invoice_number": existing_sale.invoice_number,
                    "message": "هذه العملية تمت مزامنتها مسبقًا."
                })
                continue

            try:
                with transaction.atomic():
                    payment_currency_code = sale_data.get("payment_currency", "USD")
                    pricing_currency_code = sale_data.get("pricing_currency", "USD")
                    exchange_rate = Decimal(str(sale_data.get("exchange_rate", "1")))
                    discount_amount = Decimal(str(sale_data.get("discount_amount", "0")))
                    notes = sale_data.get("notes", "") or ""

                    pricing_currency = Currency.objects.get(code=pricing_currency_code)
                    payment_currency = Currency.objects.get(code=payment_currency_code)

                    items_data = sale_data.get("items", [])
                    if not items_data:
                        raise ValueError("لا توجد بنود داخل عملية البيع.")

                    # تحقق من المنتجات والمخزون
                    product_ids = [item.get("product_id") for item in items_data]
                    products = Product.objects.filter(
                        merchant=merchant,
                        id__in=product_ids
                    )
                    products_map = {p.id: p for p in products}

                    for item in items_data:
                        product_id = item.get("product_id")
                        quantity = int(item.get("quantity", 0))

                        product = products_map.get(product_id)
                        if not product:
                            raise ValueError(f"المنتج {product_id} غير موجود.")

                        if quantity <= 0:
                            raise ValueError(f"الكمية غير صالحة للمنتج {product.name}.")

                        if product.stock_quantity < quantity:
                            raise ValueError(f"المخزون غير كافٍ للمنتج {product.name}.")

                    sale = Sale.objects.create(
                        merchant=merchant,
                        customer=None,
                        invoice_number=generate_invoice_number(),
                        offline_id=offline_id,
                        payment_type="cash",
                        payment_status="paid",
                        created_by=request.user,
                        notes=notes,
                        pricing_currency=pricing_currency,
                        payment_currency=payment_currency,
                        exchange_rate=exchange_rate,
                        discount_amount=discount_amount,
                    )

                    for item in items_data:
                        product_id = item.get("product_id")
                        quantity = int(item.get("quantity", 0))
                        unit_price = Decimal(str(item.get("unit_price", "0")))
                        unit_cost = Decimal(str(item.get("unit_cost", "0")))

                        product = products_map[product_id]

                        SaleItem.objects.create(
                            sale=sale,
                            product=product,
                            quantity=quantity,
                            unit_price=unit_price,
                            unit_cost=unit_cost,
                        )

                        product.stock_quantity -= quantity
                        product.save(update_fields=["stock_quantity"])

                        InventoryTransaction.objects.create(
                            merchant=merchant,
                            product=product,
                            transaction_type="sale",
                            quantity=-quantity,
                            reference_sale=sale,
                            note=f"Offline Sync Sale {sale.invoice_number}",
                        )

                    sale.recalculate_totals()
                    sale.save()

                    Payment.objects.create(
                        sale=sale,
                        customer=sale.customer if sale.customer else None,
                        merchant=merchant,
                        amount=sale.total_amount,
                        original_amount=sale.total_amount_payment_currency,
                        note="دفعة نقدية من مزامنة أوفلاين",
                        created_by=request.user,
                        currency=payment_currency,
                        exchange_rate=exchange_rate,
                    )

                    sale.recalculate_totals()
                    sale.save()

                    results.append({
                        "offline_id": offline_id,
                        "ok": True,
                        "status": "synced",
                        "sale_id": sale.id,
                        "invoice_number": sale.invoice_number,
                        "message": "تمت مزامنة العملية بنجاح."
                    })

            except Currency.DoesNotExist:
                results.append({
                    "offline_id": offline_id,
                    "ok": False,
                    "message": "عملة غير موجودة في النظام."
                })
            except Exception as e:
                results.append({
                    "offline_id": offline_id,
                    "ok": False,
                    "message": str(e)
                })

        return JsonResponse({
            "ok": True,
            "results": results
        }, json_dumps_params={"ensure_ascii": False})    


