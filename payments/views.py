import requests
import hashlib
import hmac
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect , render
from .models import Payment
from shipments.models import Shipment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Receipt
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView 
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.


# def process_payment_view(request, shipment_id):
#     """
#     Handle a user's payment for a shipment.
#     """
#     shipment = get_object_or_404(Shipment, id=shipment_id, user=request.user)

#     payment = shipment.payments

#     if not payment:
#         messages.error(request, "No payment record found for this shipment")
#         return redirect("shipments:detail", pk=shipment.id)
    
#     elif payment.status == "PAID":
#          messages.info(request, "This shipment is already paid for!")
#          return redirect("shipments:detail", pk=shipment.id)
    
#     receipt = payment.mark_paid()
#     messages.success(request, f"payment successful! Receipt: {receipt.receipt_number}")
#     return redirect("shipments:detail", pk=shipment.id)

@login_required(login_url="users:login")
def receipt_view(request, shipment_id):
    shipment = Shipment.objects.get(id=shipment_id)
    receipt = shipment.payments.receipt
    return render(request, "payments/receipt.html",{"receipt" : receipt})

@login_required(login_url="users:login")
def download_receipt_pdf(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk)
    html_string = render_to_string("payments/receipt.html", {"receipt": receipt})

    pdf_file = HTML(string=html_string, base_url=f"http://127.0.0.1:8000/").write_pdf()
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename='receipt_{receipt.receipt_number}.pdf"
    return response


@login_required(login_url="users:login")
def initiate_payment_view(request, pk):
    """
    Initiates a payment with flutterwave and redirects the user to the checkout page.
    """

    payment = get_object_or_404(Payment, pk=pk, user=request.user)

    if payment.status == "PAID":
        messages.info(request, "This shipment is already paid for.")
        return redirect("shipments:detail", pk=payment.shipment.pk)

    #If payment previously failed, generate a new tx_ref for retry
    elif payment.status == "FAILED":
        payment.refresh_tx_ref()

    #Build payload form the model helper method
    payload = payment.get_flutterwave_payload()

    headers = {
        "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    url = "https://api.flutterwave.com/v3/payments"
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if data.get("status") == "success":
        checkout_url = data["data"]["link"]
        return redirect(checkout_url)
    else:
        messages.error(request, "Error initialising payment. Please try again.")
        return redirect("shipments:detail", pk=payment.shipment.pk)
    
@login_required(login_url="users:login")
def verify_payment_view(request):
    """
    Handles Flutterwave's redirect after payment and verify transaction status.
    """

    status = request.GET.get("status")
    tx_ref = request.GET.get("tx_ref")
    transaction_id = request.GET.get("transaction_id")

    #find the payment object 
    payment = get_object_or_404(Payment, tx_ref=tx_ref, user=request.user)

    if status != "successful":
        #Mark as failed
        payment.mark_failed(transaction_id=transaction_id, meta={"reason":status})
        messages.error(request, "Payment was not successful.")
        return redirect("shipments:detail", pk=payment.shipment.pk)
    
    #Verify payment with flutterwave API
    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
    headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}
    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("status") == "success" and data["data"]["tx_ref"] == tx_ref:
        payment.mark_paid(transaction_id=transaction_id, meta=data['data'])
        messages.success(request, "Payment for shipment successful.")
    else:
        payment.mark_failed(transaction_id=transaction_id, meta=data)
        messages.error(request, "Payment verificaton failed.")
    return redirect("shipments:detail", pk=payment.shipment.pk)

class PaymentHistoryView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = "payments/payment_history.html"
    context_object_name = "payments"
    paginate_by = 10

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by("-created_at")
        return super().get_queryset()