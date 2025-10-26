"""
defining views(processes requests and returns appropriate responses) for the payments app
"""

import requests
import hashlib
import hmac
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
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
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator


@login_required(login_url="users:login")  # login page if not authenticated (using decorators)
def receipt_view(request, shipment_id):
    """ processes request for receipt page """
    shipment = get_object_or_404(Shipment,id=shipment_id, user=request.user)  # gets shipment instance
    receipt = shipment.payment.receipt  # gets the receipt instance for that related shipment instance
    return render(request, "payments/receipt.html", {"receipt": receipt})  # renders the receipt  page


@login_required(login_url="users:login")  # login page if not authenticated (using decorators)
def download_receipt_pdf(request, pk):
    """process requests to download receipts """
    receipt = get_object_or_404(Receipt, pk=pk, payment__user=request.user)  # gets receipt instance
    html_string = render_to_string("payments/receipt.html", {"receipt": receipt})  # parses html template to string

    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri(
        '/')).write_pdf()  # creates a pdf file with weasywrite HTML object
    response = HttpResponse(pdf_file, content_type="application/pdf")  # generates a response with attached pdf file
    response[
        "Content-Disposition"] = f"attachment; filename='receipt_{receipt.receipt_number}.pdf"  # names attached pdf file with specified filename
    return response  # returns the attached pdf-file to be downloaded


@ratelimit(key='ip', rate='3/m', block=False) # security measure to block brute forcing
@login_required(login_url="users:login")  # login page if not authenticated (using decorators)
def initiate_payment_view(request, pk):
    """
    processes Initiation of  payment with flutterwave payment gateway
    and redirects the user to the checkout page.
    """

    #show friendly message on too many requests
    if getattr(request, 'limited', False):
        messages.error(request, 'Too many payment attempts. Please wait a minute.')
        return redirect('payments:payments-history')

    payment = get_object_or_404(Payment, pk=pk, user=request.user)  # gets Payment instance
    if payment.status == "PAID":
        """if already paid route back to detail page for the shipment"""
        messages.info(request, "This shipment is already paid for.")
        return redirect("shipments:detail", pk=payment.shipment.pk)

    # If payment previously failed, generate a new tx_ref for retry
    elif payment.status == "FAILED":
        """if payment has status failed refresh the 
            tx_ref, transaction_id and meta field as 
            implemented in the 'refresh_tx_ref()' method
        """
        payment.refresh_tx_ref()

    payload = payment.get_flutterwave_payload()  # Build payload from the model helper method
    headers = {
        "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
        "Content-Type": "application/json"
    }  # set header content for flutterwave authentication

    url = "https://api.flutterwave.com/v3/payments"  # flutterwave api endpoint
    
    try:
        response = requests.post(url, json=payload, headers=headers)  # posts payload and headers to flutterwave api
        # endpoint
        data = response.json()  # retrieve metadata in json format from flutterwave api endpoint

        if data.get("status") == "success":
            """ on successful initialisation of payment route to flutterwave payment page (checkout page)"""
            checkout_url = data["data"]["link"]  # retrieves the checkout page url
            return redirect(checkout_url)  # redirects to flutterwave checkout age
        else:
            """on failed initialisation show error message """
            messages.error(request, "Error initialising payment. Please try again.")  # sends message to displayed page
            return redirect("shipments:detail", pk=payment.shipment.pk)  # redirect to shipment detail page
    except ValueError:
        # handles .json() decoding failure 
        messages.error(request, 'Received invalid response from payment gateway')
        return redirect('shipments:detail', pk=payment.shipment.pk)
    except Exception as e:
        # handles network errors, timeouts , etc.
        messages.error(request, f"Error connecting to payment gateway please try again later")
        return redirect('shipments:detail', pk=payment.shipment.pk)

@ratelimit(key='ip', rate='10/m', block=False) # security measure to block brute forcing 
@login_required(login_url="users:login")  # login page if not authenticated(using decorators)
def verify_payment_view(request):
    """
    processes  Flutterwave redirect after payment and verifies transaction status.
    """
    if getattr(request, 'limited', False):
        messages.error(request, 'Too many verification attempts. Please try again later.')
        return redirect('home')  # or appropriate page
    
    # ... rest of code

    status = request.GET.get("status")  # get status parameter from flutterwave
    tx_ref = request.GET.get("tx_ref")  # get tx_ref value from flutterwave
    transaction_id = request.GET.get("transaction_id")  # get transaction_id for transaction from flutterwave

    payment = get_object_or_404(Payment, tx_ref=tx_ref, user=request.user)  # find the payment object

    if status != "successful":
        """on failed verification mark payment instance as failed """
        payment.mark_failed(transaction_id=transaction_id, meta={"reason": status})  # mark as failed
        messages.error(request, "Payment was not successful.")  # sends error message to displayed page
        return redirect("shipments:detail", pk=payment.shipment.pk)  # redirects to shipment detail page

    # Verify payment with flutterwave API
    url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"  # verification api
    headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}  # authenticating

    try:
        response = requests.get(url, headers=headers)  # post header to verification api url
        data = response.json()  # retrieve metadata from response
    except Exception as e:
        logger = logging.getLogger(__name__)  # Move this to the TOP of the file
        logger.error(f"Error verifying payment please try again later")
        payment.mark_failed(transaction_id=transaction_id, meta={'error': str(e)})
        messages.error(request, "Payment verification failed. Please contact support.")
        return redirect("shipments:detail", pk=payment.shipment.pk)
    
    if data.get("status") == "success" and data["data"]["tx_ref"] == tx_ref:
        """check if payment successful on flutterwave api 
            and the tx_ref values are the same 
            then it marks Payment instance as paid        
        """
        payment.mark_paid(transaction_id=transaction_id, meta=data['data'])  # mark as paid
        messages.success(request, "Payment for shipment successful.")  # sends success message to displayed page
    else:
        """if verification status is not success 
            or the tx_ref values do not match for the payment 
            then it marks Payment instance as failed
        """
        payment.mark_failed(transaction_id=transaction_id, meta=data)  # mark as failed
        messages.error(request, "Payment verificaton failed.")  # sends error message to displayed page
    return redirect("shipments:detail", pk=payment.shipment.pk)  # redirects to shipment detail page


logger = logging.getLogger(__name__)  # setting logger


@csrf_exempt 
@require_POST
def flutterwave_webhook_view(request):
    """
    processes webhook support for flutterwave payments
    """
    try:
        signature = request.headers.get('verif-hash')
        expected_signature = settings.FLW_SECRET_HASH

        if not signature or not hmac.compare_digest(signature, expected_signature):
            logger.warning("Invalid webhook signature")
            return JsonResponse({'status': 'error'}, status=403)

        payload = json.loads(request.body)
        data = payload.get('data', {})
        tx_ref = data.get('tx_ref')
        transaction_id = data.get('transaction_id')
        status = data.get('status', '').lower()

        logger.info(f"Webhook received: tx_ref={tx_ref}, transaction_id={transaction_id}, status={status}")

        try:
            payment = Payment.objects.get(tx_ref=tx_ref)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: tx_ref={tx_ref}, transaction_id={transaction_id}")
            return JsonResponse({'status': 'No record of Payment'}, status=404)

        if status == 'successful':
            if payment.status != 'PAID':
                payment.mark_paid(transaction_id=transaction_id, meta=payload)
                logger.info(f"Payment marked as PAID: tx_ref={tx_ref}")
                return JsonResponse({'status': 'Received'}, status=200)
            else:
                logger.info(f'payment alread PAID: tx_ref={tx_ref}')
                return JsonResponse({'status': 'Already processed'}, status=200)
            
        else:
            if payment.status != 'FAILED':
                payment.mark_failed(transaction_id=transaction_id, meta=payload)
                logger.warning(f"Payment marked as FAILED: tx_ref={tx_ref}, reason={status}")
                return JsonResponse({'status': 'Failed'}, status=403)
            else:
                logger.info(f'payment already FAILED: tx_ref={tx_ref}')
                return JsonResponse({'status': 'Already processed'}, status=200)

    except Exception as e:
        logger.exception("Unhandled exception in webhook")
        return JsonResponse({'status': 'Internal server error'}, status=500)



class PaymentHistoryView(LoginRequiredMixin, ListView):
    """
    processes requests for payment history page
    """
    login_url= 'users:login'
    model = Payment  # binds view to Payment model
    template_name = "payments/payment_history.html"  # template to render
    context_object_name = "payments"  # context reference in template for returned queryset
    paginate_by = 10  # value to paginate template by

    def get_queryset(self):
        """returns payment instances(rows) with status 'PAID' for the user """
        return Payment.objects.filter(user=self.request.user, status="PAID").order_by("-created_at")
