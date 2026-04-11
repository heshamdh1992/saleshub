from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView
from apps.core.mixins import OwnerRequiredMixin
from .forms import MerchantForm
from .models import Merchant


class MerchantDetailView(LoginRequiredMixin,OwnerRequiredMixin, DetailView):
    model = Merchant
    template_name = "merchants/detail.html"
    context_object_name = "merchant"

    def get_object(self, queryset=None):
        return self.request.user.staff_profile.merchant


class MerchantUpdateView(LoginRequiredMixin,OwnerRequiredMixin, UpdateView):
    model = Merchant
    form_class = MerchantForm
    template_name = "merchants/form.html"
    context_object_name = "merchant"
    success_url = reverse_lazy("merchants:current")

    def get_object(self, queryset=None):
        return self.request.user.staff_profile.merchant

    def form_valid(self, form):
        messages.success(self.request, "تم تحديث إعدادات المتجر بنجاح.")
        return super().form_valid(form)