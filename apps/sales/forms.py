from django import forms
from apps.currencies.models import Currency
from .models import Payment


class PaymentForm(forms.ModelForm):
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True).order_by("code"),
        label="عملة الدفع",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Payment
        fields = ["amount", "currency", "note"]
        labels = {
            "amount": "قيمة الدفعة",
            "note": "ملاحظة",
        }
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }