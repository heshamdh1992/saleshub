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
import base64
from io import BytesIO
from django.http import HttpResponse
from barcode import Code128
from barcode.writer import ImageWriter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


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


class ProductExportExcelView(LoginRequiredMixin, ManagerOrOwnerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        merchant = self.get_merchant()

        products = Product.objects.filter(
            merchant=merchant,
            is_active=True
        ).order_by("name")

        wb = Workbook()
        ws = wb.active
        ws.title = "Products"

        headers = [
            "اسم المنتج",
            "SKU",
            "الباركود",
            "سعر البيع USD",
            "سعر التكلفة USD",
            "المخزون الحالي",
            "حد التنبيه",
            "حالة المخزون",
        ]

        ws.append(headers)

        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        for product in products:
            if product.stock_quantity <= 0:
                stock_status = "نفد المخزون"
            elif product.stock_quantity <= product.reorder_level:
                stock_status = "مخزون منخفض"
            else:
                stock_status = "جيد"

            ws.append([
                product.name,
                product.sku or "",
                product.barcode or "",
                float(product.base_price_usd or 0),
                float(product.cost_price_usd or 0),
                product.stock_quantity,
                product.reorder_level,
                stock_status,
            ])

        column_widths = {
            "A": 30,
            "B": 18,
            "C": 22,
            "D": 16,
            "E": 16,
            "F": 16,
            "G": 16,
            "H": 18,
        }

        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="products.xlsx"'

        return response

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

    def generate_barcode_base64(self, barcode_value):
        buffer = BytesIO()

        barcode_obj = Code128(str(barcode_value), writer=ImageWriter())
        barcode_obj.write(
            buffer,
            options={
                "write_text": False,
                "module_width": 0.35,
                "module_height": 9,
                "quiet_zone": 1.5,
                "font_size": 0,
                "text_distance": 0,
                "dpi": 300,
            }
        )

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        copies = self.request.GET.get("copies", "1")

        try:
            copies = int(copies)
        except ValueError:
            copies = 1

        copies = max(1, min(copies, 100))

        product = self.object

        if not product.barcode:
            product.barcode = product.generate_internal_barcode_value()
            product.save(update_fields=["barcode"])

        context["barcode_base64"] = self.generate_barcode_base64(product.barcode)
        context["copies_range"] = range(copies)
        context["copies"] = copies

        return context