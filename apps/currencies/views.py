from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, View
from apps.core.mixins import OwnerRequiredMixin
from .forms import CurrencyForm, ExchangeRateForm
from .models import Currency, ExchangeRate


class CurrencyListView(LoginRequiredMixin,OwnerRequiredMixin, ListView):
    model = Currency
    template_name = "currencies/currency_list.html"
    context_object_name = "currencies"

    def get_queryset(self):
        return Currency.objects.all().order_by("code")


class CurrencyCreateView(LoginRequiredMixin,OwnerRequiredMixin, CreateView):
    model = Currency
    form_class = CurrencyForm
    template_name = "currencies/currency_form.html"
    success_url = reverse_lazy("currencies:currency_list")

    def form_valid(self, form):
        messages.success(self.request, "تمت إضافة العملة بنجاح.")
        return super().form_valid(form)


class CurrencyUpdateView(LoginRequiredMixin,OwnerRequiredMixin, UpdateView):
    model = Currency
    form_class = CurrencyForm
    template_name = "currencies/currency_form.html"
    success_url = reverse_lazy("currencies:currency_list")

    def form_valid(self, form):
        messages.success(self.request, "تم تعديل العملة بنجاح.")
        return super().form_valid(form)


class ExchangeRateListView(LoginRequiredMixin,OwnerRequiredMixin, ListView):
    model = ExchangeRate
    template_name = "currencies/exchange_rate_list.html"
    context_object_name = "rates"

    def get_queryset(self):
        return ExchangeRate.objects.select_related("base_currency", "quote_currency").order_by(
            "base_currency__code", "quote_currency__code", "-created_at"
        )


class ExchangeRateCreateView(LoginRequiredMixin,OwnerRequiredMixin, CreateView):
    model = ExchangeRate
    form_class = ExchangeRateForm
    template_name = "currencies/exchange_rate_form.html"
    success_url = reverse_lazy("currencies:rate_list")

    def form_valid(self, form):
        with transaction.atomic():
            base_currency = form.cleaned_data["base_currency"]
            quote_currency = form.cleaned_data["quote_currency"]
            is_active = form.cleaned_data.get("is_active", False)

            if is_active:
                ExchangeRate.objects.filter(
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    is_active=True
                ).update(is_active=False)

            messages.success(self.request, "تمت إضافة سعر الصرف بنجاح.")
            return super().form_valid(form)


class ExchangeRateUpdateView(LoginRequiredMixin,OwnerRequiredMixin, UpdateView):
    model = ExchangeRate
    form_class = ExchangeRateForm
    template_name = "currencies/exchange_rate_form.html"
    success_url = reverse_lazy("currencies:rate_list")

    def form_valid(self, form):
        with transaction.atomic():
            base_currency = form.cleaned_data["base_currency"]
            quote_currency = form.cleaned_data["quote_currency"]
            is_active = form.cleaned_data.get("is_active", False)

            if is_active:
                ExchangeRate.objects.filter(
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    is_active=True
                ).exclude(pk=self.object.pk).update(is_active=False)

            messages.success(self.request, "تم تعديل سعر الصرف بنجاح.")
            return super().form_valid(form)


class ExchangeRateActivateView(LoginRequiredMixin, OwnerRequiredMixin,View):
    def post(self, request, pk):
        rate = ExchangeRate.objects.select_related("base_currency", "quote_currency").get(pk=pk)

        with transaction.atomic():
            ExchangeRate.objects.filter(
                base_currency=rate.base_currency,
                quote_currency=rate.quote_currency,
                is_active=True
            ).exclude(pk=rate.pk).update(is_active=False)

            rate.is_active = True
            rate.save(update_fields=["is_active"])

        messages.success(request, "تم تفعيل سعر الصرف.")
        return redirect("currencies:rate_list")