from django.urls import path
from .views import (
    SalesReportView,
    ProductReportView,
    CustomerReportView,
    SalesReportExportExcelView,
    ProductReportExportExcelView,
    CustomerReportExportExcelView,
    
)

app_name = "reports"

urlpatterns = [
    path("sales/", SalesReportView.as_view(), name="sales_report"),
    path("products/", ProductReportView.as_view(), name="product_report"),
    path("customers/", CustomerReportView.as_view(), name="customer_report"),
    path("sales/export/excel/", SalesReportExportExcelView.as_view(), name="sales_report_export_excel"),
    path("products/export/excel/", ProductReportExportExcelView.as_view(), name="product_report_export_excel"),
    path("customers/export/excel/", CustomerReportExportExcelView.as_view(), name="customer_report_export_excel"),
    
]