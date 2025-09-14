from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect 
from .models import Payment
from shipments.models import Shipment
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
def process_payment_view(request, shipment_id):
    """
    Handle a user's payment for a shipment.
    """
    shipment = get_object_or_404(Shipment, id=shipment_id, user=request.user)

    payment = shipment.payments

    if not payment:
        messages.error(request, "No payment record found for this shipment")
        return redirect("shipments:detail", pk=shipment.id)
    
    elif payment.status == "PAID":
         messages.info(request, "This shipment is already paid for!")
         return redirect("shipments:detail", pk=shipment.id)
    
    receipt = payment.mark_paid()
    messages.success(request, f"payment successful! Receipt: {receipt.receipt_number}")
    return redirect("shipments:detail", pk=shipment.id)

