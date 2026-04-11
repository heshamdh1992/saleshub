from django import forms
from .models import Merchant


class MerchantForm(forms.ModelForm):
    class Meta:
        model = Merchant
        fields = ["name", "phone", "address", "logo", "invoice_note", "is_active"]
        labels = {
            "name": "اسم المتجر",
            "phone": "الهاتف",
            "address": "العنوان",
            "logo": "الشعار",
            "invoice_note": "ملاحظة أسفل الفاتورة",
            "is_active": "نشط",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "invoice_note": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }