from django.db import models
from apps.core.models import TimeStampedModel
import os
from io import BytesIO

from django.core.files.base import ContentFile
from barcode import Code128
from barcode.writer import ImageWriter

class Product(TimeStampedModel):
    merchant = models.ForeignKey(
        "merchants.Merchant",
        on_delete=models.CASCADE,
        related_name="products"
    )
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    base_price_usd = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    stock_quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=0)   # هذا هو حد التنبيه
    barcode_image = models.ImageField(upload_to="barcodes/", blank=True, null=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name

    @property
    def stock_status(self):
        if self.stock_quantity <= 0:
            return "out"
        if self.stock_quantity <= self.reorder_level:
            return "low"
        return "ok"
    def generate_internal_barcode_value(self):
        if self.barcode:
            return self.barcode

        if not self.pk:
            raise ValueError("يجب حفظ المنتج أولًا قبل توليد الباركود.")

        return f"P{self.pk:06d}"

    def generate_barcode_image(self, save_model=True):
        barcode_value = self.generate_internal_barcode_value()

        buffer = BytesIO()
        barcode_obj = Code128(barcode_value, writer=ImageWriter())

        barcode_obj.write(
            buffer,
            options={
                "write_text": True,
                "module_width": 0.25,
                "module_height": 15,
                "quiet_zone": 2.5,
                "font_size": 10,
                "text_distance": 2,
            }
        )

        filename = f"{barcode_value}.png"
        self.barcode = barcode_value
        self.barcode_image.save(filename, ContentFile(buffer.getvalue()), save=False)

        if save_model:
            self.save(update_fields=["barcode", "barcode_image"])

        return self.barcode_image