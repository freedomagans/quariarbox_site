from django.urls import path
from .views import *
app_name = "payments"
urlpatterns = [
    path("receipt/<int:shipment_id>",receipt_view, name="receipt"),
    path("receipt/download/<int:pk>", download_receipt_pdf, name="download-receipt"),
    path("initiate/<int:pk>", initiate_payment_view, name="initiate"),
    path("verify/", verify_payment_view, name="verify"),
    path("history/", PaymentHistoryView, name="payment-history")
]
