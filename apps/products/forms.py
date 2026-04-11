from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "barcode",
            "base_price_usd",
            "cost_price_usd",
            "stock_quantity",
            "reorder_level",
            "is_active",
        ]
        labels = {
            "name": "اسم المنتج",
            "sku": "SKU",
            "barcode": "الباركود",
            "base_price_usd": "سعر البيع المرجعي (USD)",
            "cost_price_usd": "تكلفة الشراء (USD)",
            "stock_quantity": "الكمية الحالية",
            "reorder_level": "حد التنبيه",
            "is_active": "نشط",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "اسم المنتج"}),
            "sku": forms.TextInput(attrs={"class": "form-control", "placeholder": "SKU"}),
            "barcode": forms.TextInput(attrs={"class": "form-control", "placeholder": "الباركود", "id": "barcode-input"}),
            "base_price_usd": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "cost_price_usd": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "reorder_level": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.merchant = kwargs.pop("merchant", None)
        super().__init__(*args, **kwargs)

    def clean_sku(self):
        sku = self.cleaned_data.get("sku")
        if sku and self.merchant:
            qs = Product.objects.filter(merchant=self.merchant, sku=sku)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("هذا الـ SKU مستخدم مسبقًا داخل هذا المحل.")
        return sku

    def clean_barcode(self):
        barcode = self.cleaned_data.get("barcode")
        if barcode and self.merchant:
            qs = Product.objects.filter(merchant=self.merchant, barcode=barcode)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("هذا الباركود مستخدم مسبقًا داخل هذا المحل.")
        return barcode