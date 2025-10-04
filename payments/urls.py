from django.urls import path
from .views import *

app_name = "payments"  # app name

# list of urls
urlpatterns = [
    path("receipt/<int:shipment_id>", receipt_view, name="receipt"),  # url for receipt page
    path("receipt/download/<int:pk>", download_receipt_pdf, name="download-receipt"),  # url for downloading receipts
    path("initiate/<int:pk>", initiate_payment_view, name="initiate"),  # url for initiating payment on payment gateway
    path("verify/", verify_payment_view, name="verify"),  # url for verifying payment on payment gateway
    path("history/", PaymentHistoryView.as_view(), name="payments-history"),  # url for payment history page
    path("webhook/", flutterwave_webhook_view, name='webhook')  # url for webhook support
]
