from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from apps.core.mixins import CashierOrAboveRequiredMixin, ManagerOrOwnerRequiredMixin
from apps.core.mixins import MerchantRequiredMixin
from .models import Customer
from .forms import CustomerForm


class CustomerListView(LoginRequiredMixin, CashierOrAboveRequiredMixin, ListView):
    model = Customer
    template_name = "customers/list.html"
    context_object_name = "customers"
    paginate_by = 20

    def get_queryset(self):
        merchant = self.get_merchant()
        q = self.request.GET.get("q", "").strip()

        qs = Customer.objects.filter(merchant=merchant)

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(phone__icontains=q)
            )

        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class CustomerCreateView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/form.html"
    success_url = reverse_lazy("customers:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["merchant"] = self.get_merchant()
        return kwargs

    def form_valid(self, form):
        form.instance.merchant = self.get_merchant()
        messages.success(self.request, "تمت إضافة العميل بنجاح.")
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = "customers/form.html"
    success_url = reverse_lazy("customers:list")

    def get_queryset(self):
        return Customer.objects.filter(merchant=self.get_merchant())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["merchant"] = self.get_merchant()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "تم تعديل العميل.")
        return super().form_valid(form)


class CustomerDetailView(LoginRequiredMixin, CashierOrAboveRequiredMixin, DetailView):
    model = Customer
    template_name = "customers/detail.html"
    context_object_name = "customer"

    def get_queryset(self):
        return Customer.objects.filter(
            merchant=self.get_merchant()
        ).prefetch_related("sales", "payments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object

        entries = []

        unpaid_sales = customer.sales.filter(
            payment_type="debt"
        ).exclude(
            payment_status="paid"
        ).order_by("-created_at")

        for sale in customer.sales.all():
            entries.append({
                "date": sale.created_at,
                "type": "invoice",
                "reference": sale.invoice_number,
                "debit": sale.total_amount,
                "credit": 0,
                "balance_currency_note": f"{sale.payment_currency.code if sale.payment_currency else 'USD'} {sale.total_amount_payment_currency}",
                "sale_id": sale.id,
            })

        for payment in customer.payments.all():
            entries.append({
                "date": payment.created_at,
                "type": "payment",
                "reference": f"دفعة على الفاتورة {payment.sale.invoice_number}",
                "debit": 0,
                "credit": payment.amount,
                "balance_currency_note": f"{payment.currency.code if payment.currency else 'USD'} {payment.original_amount}",
                "sale_id": payment.sale_id,
            })

        entries.sort(key=lambda x: x["date"])

        running_balance = 0
        for entry in entries:
            running_balance += float(entry["debit"]) - float(entry["credit"])
            entry["balance"] = running_balance

        context["entries"] = entries
        context["unpaid_sales"] = unpaid_sales
        return context