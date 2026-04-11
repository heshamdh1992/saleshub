from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "notes", "is_active"]
        labels = {
            "name": "اسم العميل",
            "phone": "رقم الهاتف",
            "notes": "ملاحظات",
            "is_active": "نشط",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "اسم العميل"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "رقم الهاتف"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        self.merchant = kwargs.pop("merchant", None)
        super().__init__(*args, **kwargs)

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and self.merchant:
            qs = Customer.objects.filter(merchant=self.merchant, phone=phone)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("هذا الرقم مستخدم مسبقًا داخل هذا المحل.")
        return phone