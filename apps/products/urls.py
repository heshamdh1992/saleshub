from django.urls import path
from .views import (
    ProductListView,
    ProductCreateView,
    ProductUpdateView,
    ProductDetailView,
    BarcodeScannerView,
)
from .views import GenerateBarcodeView, ProductLabelPrintView
app_name = "products"

urlpatterns = [
    path("", ProductListView.as_view(), name="list"),
    path("add/", ProductCreateView.as_view(), name="add"),
    path("<int:pk>/", ProductDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", ProductUpdateView.as_view(), name="edit"),
    path("scanner/", BarcodeScannerView.as_view(), name="scanner"),
    path("<int:pk>/generate-barcode/", GenerateBarcodeView.as_view(), name="generate_barcode"),
    path("<int:pk>/label/", ProductLabelPrintView.as_view(), name="label_print"),

]