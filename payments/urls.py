from django.urls import path
from .views import *
app_name = "payments"
urlpatterns = [
    path("<int:shipment_id>",process_payment_view, name="process-payment"),
    path("receipt/<int:shipment_id>",receipt_view, name="receipt"),
    path("receipt/download/<int:pk>", download_receipt_pdf, name="download-receipt")
]
