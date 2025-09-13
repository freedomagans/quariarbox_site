import uuid
from django.db import models
from django.conf import settings 
from django.urls import reverse
from django.utils import timezone
#from shipments.models import Shipment

# Create your models here.
class Payment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded")
    ]

    METHOD_CHOICES = [
        ("CARD", "Card"),
        ("CASH", "Cash"),
        ("MOBILE", "Mobile Money"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    shipment = models.OneToOneField("shipments.Shipment", on_delete=models.CASCADE,related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="CARD")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="PENDING")
    transaction_id = models.CharField(max_length=128, blank=True, null=True)
    meta = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Payment for {self.shipment.tracking_number} - {self.status}"
    
    def generate_transaction_id(self):
        return uuid.uuid4().hex.upper()
    
    def mark_paid(self, transaction_id=None, meta=None, create_receipt=True):
        if not transaction_id:
            transaction_id = self.generate_transaction_id()
        self.transaction_id = transaction_id
        if meta is not None:
            self.meta = meta 
        self.status = "PAID"
        self.updated_at = timezone.now()
        self.save(update_fields=["transaction_id", "meta", "status", "updated_at"])

        receipt = None
        if create_receipt:
            receipt = Receipt.objects.create(payment=self)
        return receipt
    

    def mark_failed(self, transaction_id=None, meta=None):
        if transaction_id:
            self.transaction_id = transaction_id

        if meta is not None:
            self.meta = meta

        self.status = "FAILED"
        self.updated_at = timezone.now()
        self.save(update_fields=["transaction_id", "meta", "status", "updated_at"])


class Receipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name="receipt")
    receipt_number = models.CharField(max_length=40, unique=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to="receipts/", blank=True, null=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Receipt {self.receipt_number}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            ts = timezone.now().strftime("%Y%m%d%H%M%S")
            short = uuid.uuid4().hex[:6].upper()
            self.receipt_number = f"RCP-{ts}-{short}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("payments:receipt", kwargs={"pk": self.pk})
    