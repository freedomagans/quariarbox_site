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

def receipt_view(request, shipment_id):
    shipment = Shipment.objects.get(id=shipment_id)
    receipt = shipment.payments.receipt
    return render(request, "payments/receipt.html",{"receipt" : receipt})

def download_receipt_pdf(request, pk):
    receipt = get_object_or_404(Receipt, pk=pk)
    html_string = render_to_string("payments/receipt.html", {"receipt": receipt})

    pdf_file = HTML(string=html_string, base_url=f"http://127.0.0.1:8000/").write_pdf()
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename='receipt_{receipt.receipt_number}.pdf"
    return response