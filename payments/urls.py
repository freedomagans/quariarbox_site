from django.urls import path
from .views import process_payment_view
app_name = "payments"
urlpatterns = [
    path("<int:shipment_id>",process_payment_view, name="process-payment")
]
