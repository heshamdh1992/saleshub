from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.urls import reverse
from apps.core.mixins import ManagerOrOwnerRequiredMixin
from .forms import ProductForm
from .models import Product
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, TemplateView


class ProductListView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, ListView):
    model = Product
    template_name = "products/list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        merchant = self.get_merchant()
        query = self.request.GET.get("q", "").strip()

        qs = Product.objects.filter(merchant=merchant).order_by("name")

        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(barcode__icontains=query)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class ProductCreateView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "products/form.html"

    def form_valid(self, form):
        form.instance.merchant = self.get_merchant()

        response = super().form_valid(form)

        product = self.object

        # 🔥 توليد باركود تلقائي إذا لم يوجد
        if not product.barcode:
            product.generate_barcode_image(save_model=True)

        messages.success(self.request, "تم إنشاء المنتج بنجاح.")

        return response

    def get_success_url(self):
        return reverse("products:detail", kwargs={"pk": self.object.pk})


class ProductUpdateView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "products/form.html"
    success_url = reverse_lazy("products:list")

    def get_queryset(self):
        return Product.objects.filter(merchant=self.get_merchant())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["merchant"] = self.get_merchant()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "تم تعديل المنتج بنجاح.")
        return super().form_valid(form)


class ProductDetailView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, DetailView):
    model = Product
    template_name = "products/detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(merchant=self.get_merchant())


class BarcodeScannerView(LoginRequiredMixin, TemplateView):
    template_name = "products/scanner.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mode = self.request.GET.get("mode", "add").strip().lower()
        if mode not in ["add", "search", "pos"]:
            mode = "add"
        context["mode"] = mode
        return context
    
class GenerateBarcodeView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(
            Product,
            pk=pk,
            merchant=self.get_merchant()
        )

        try:
            product.generate_barcode_image(save_model=True)
            messages.success(request, f"تم توليد الباركود للمنتج {product.name}.")
        except Exception as e:
            messages.error(request, f"تعذر توليد الباركود: {str(e)}")

        return redirect("products:detail", pk=product.pk)


class ProductLabelPrintView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, DetailView):
    model = Product
    template_name = "products/label_print.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(merchant=self.get_merchant())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        copies = self.request.GET.get("copies", "1")

        try:
            copies = int(copies)
        except ValueError:
            copies = 1

        if copies < 1:
            copies = 1
        if copies > 100:
            copies = 100

        if not self.object.barcode or not self.object.barcode_image:
            self.object.generate_barcode_image(save_model=True)

        context["copies_range"] = range(copies)
        context["copies"] = copies
        return context    