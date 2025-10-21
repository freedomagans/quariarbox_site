"""
defining models for payments app to model entities that are to be stored in the database
"""

import uuid
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from weasyprint import HTML
from django.template.loader import render_to_string
import tempfile
import os


# from shipments.models import Shipment


class Payment(models.Model):
    """defines model for the Payment entity"""

    # values for status field of the model
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded")
    ]

    # values for method field of the model
    METHOD_CHOICES = [
        ("CARD", "Card"),
        ("CASH", "Cash"),
        ("MOBILE", "Mobile Money"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="payments")  # user field related to the User Model
    shipment = models.OneToOneField("shipments.Shipment", on_delete=models.CASCADE,
                                    related_name="payments")  # shipment field related to the Shipment Model(reference using string referenece 'shipments.Shipment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # cost of shipment to be paid
    method = models.CharField(max_length=20, choices=METHOD_CHOICES,
                              default="CARD")  # method field to selecet method of payment
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="PENDING")  # status field
    transaction_id = models.CharField(max_length=128, blank=True,
                                      null=True)  # transaction_id field to track transaction if needed
    tx_ref = models.CharField(max_length=100, unique=True, blank=True,
                              null=True)  # tx_ref field for referencing payment instance
    meta = models.JSONField(blank=True, null=True)  # extra data dropped by the payment gateway (flutterwave)
    created_at = models.DateTimeField(auto_now_add=True)  # date created
    updated_at = models.DateTimeField(auto_now=True)  # date updated

    class Meta:
        """save instances in order of most recent"""
        ordering = ["-created_at", '-id']  # desc order

    def __str__(self):
        return f"Payment for {self.shipment.tracking_number} - {self.status}"

    def generate_tx_ref(self):
        """generating unique tx_ref values with uuid """
        return f"QBX-{uuid.uuid4().hex[:10].upper()}"

    def mark_paid(self, transaction_id=None, meta=None, create_receipt=True):
        """
        on successful payment:

        sets status field to paid
        sets transaction_id field to passed in transaction_id from the payment gateway
        sets meta field to passed in meta info from payment gateway
        sets updated_at to time of payment.
        and generates a receipt instance 
        """
        if transaction_id:
            self.transaction_id = transaction_id
        if meta is not None:
            self.meta = meta
        self.status = "PAID"  # set status
        self.updated_at = timezone.now()  # set updated_at
        self.save(update_fields=["transaction_id", "meta", "status", "updated_at"])  # save to database

        receipt = None
        if create_receipt:
            """ 
            get receipt if payment instance has a receipt 
            but if it doen't generate one 
            """
            try:
                receipt = Receipt.objects.get(payment=self) # get receipt for payment 
            except Receipt.DoesNotExist:
                receipt = Receipt.objects.create(payment=self)  # generate receipt instance
        return receipt  # return receipt instance

    def mark_failed(self, transaction_id=None, meta=None):
        """
        on failed payment :
        sets status to failed.
        sets transaction_id to passed in transaction_id from payment gateway
        sets meta field to passed in metadata from payment gateway
        sets updated_at field 
        """
        if transaction_id:
            self.transaction_id = transaction_id  # set transaction_id

        if meta is not None:
            self.meta = meta  # set metadata
        self.status = "FAILED"  # set status
        self.updated_at = timezone.now()  # set updated date
        self.save(update_fields=["transaction_id", "meta", "status", "updated_at"])  # save to database

    def get_flutterwave_payload(self):
        """
        Build the request payload for Flutterwave payment initialisation
        """

        return {
            "tx_ref": self.tx_ref,
            "amount": str(self.amount),
            "currency": "NGN",
            "redirect_url": settings.SITE_URL + reverse("payments:verify"),
            "payment_options": "card,banktransfer",
            "customer": {"email": self.user.email, "name": self.user.get_full_name() or self.user.username},
            "customisations": {
                "title": "QuariarBox Courier",
                "description": f"Payment for shipment {self.shipment.tracking_number}",
                "logo": settings.SITE_URL + "/static/img/gallery/logo.png"
            }
        }

    def refresh_tx_ref(self):
        """
        Generate a new tx_ref and reset status to PENDING on payment retrial.
        """

        self.tx_ref = self.generate_tx_ref()  # retrieve generated tx_ref from method
        self.status = "PENDING"  # sets status to pending
        self.transaction_id = None  # sets transaction_id to None
        self.meta = None  # sets meta field to None
        self.save(update_fields=["tx_ref", "status", "transaction_id", "meta"])  # save to database

    def save(self, *args, **kwargs):
        """overriding save method so on creation of Payment instances(rows) tx_ref field is prefilled with an autogenerated tx_ref."""
        if not self.tx_ref:
            self.tx_ref = self.generate_tx_ref()  # generates tx_ref
        super().save(*args, **kwargs)


class Receipt(models.Model):
    """
    defining model for the Receipt entity 
    """

    payment = models.OneToOneField(Payment, on_delete=models.CASCADE,
                                   related_name="receipt")  # payment field related to Payment model
    receipt_number = models.CharField(max_length=40, unique=True,
                                      blank=True)  # receipt_number field to uniquely reference the Receipt instance
    issued_at = models.DateTimeField(auto_now_add=True)  # date created/issued
    pdf = models.FileField(upload_to="receipts/", blank=True,
                           null=True)  # pdf field to store reference to pdf file and generated pdfs are uploaded to the receipts folder in the media folder of the project

    class Meta:
        """saves instances(rows) in desc order based on 'issued_at' field"""
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Receipt {self.receipt_number}"

    def save(self, *args, **kwargs):
        """Generate a unique receipt number on creation of instances"""
        if not self.receipt_number:
            ts = timezone.now().strftime("%Y%m%d%H%M%S")
            short = uuid.uuid4().hex[:6].upper()
            self.receipt_number = f"RCP-{ts}-{short}"  # set receipt number field to formated generated value

        super().save(*args, **kwargs)  # Save first to get a primary key for the file path

        # Generate PDF after saving using weasyprint
        if not self.pdf:
            html_string = render_to_string("payments/receipt.html",
                                           {"receipt": self})  # gets html of template as a string value
            html = HTML(string=html_string,
                        base_url=settings.SITE_URL)  # instantiates HTML object(for weasy print) with the html_string

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
                """
                'output' is now a temporary file object 
                'delete=False' -> will remain after closing
                creates a temporary pdf file 
                """
                html.write_pdf(target=output.name)  # creates pdf with full path to temp file (output.name)
                output.flush()  # writes everything in buffer to disk

                pdf_name = f"receipt_{self.receipt_number}.pdf"  # formatted name for pdf

                self.pdf.save(pdf_name, open(output.name, 'rb'), save=False)  # set the PDF into the pdf FileField

            os.unlink(output.name)  # cleanup temp file
            super().save(update_fields=["pdf"])  # save data to databse

    def get_absolute_url(self):
        """returns the receipt page for the receipt instance"""
        return reverse("payments:receipt", kwargs={"shipment_id": self.payment.shipment.pk})
