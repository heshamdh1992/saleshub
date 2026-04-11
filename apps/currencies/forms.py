from django import forms
from .models import Currency, ExchangeRate


class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ["code", "name", "symbol", "is_active"]
        labels = {
            "code": "رمز العملة",
            "name": "اسم العملة",
            "symbol": "الرمز",
            "is_active": "نشطة",
        }
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "USD"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "US Dollar"}),
            "symbol": forms.TextInput(attrs={"class": "form-control", "placeholder": "$"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = ["base_currency", "quote_currency", "rate", "is_active"]
        labels = {
            "base_currency": "العملة الأساسية",
            "quote_currency": "العملة المقابلة",
            "rate": "سعر الصرف",
            "is_active": "فعّال",
        }
        widgets = {
            "base_currency": forms.Select(attrs={"class": "form-select"}),
            "quote_currency": forms.Select(attrs={"class": "form-select"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        base_currency = cleaned_data.get("base_currency")
        quote_currency = cleaned_data.get("quote_currency")

        if base_currency and quote_currency and base_currency == quote_currency:
            raise forms.ValidationError("لا يمكن أن تكون العملة الأساسية والمقابلة نفسها.")

        return cleaned_data