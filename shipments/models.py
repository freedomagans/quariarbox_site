from django.db import models
from django.contrib.auth.models import User
import uuid


# Create your models here.
class Shipment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("IN_TRANSIT", "In Transit"),
        ("DELIVERED", "Delivered"),
        ("CANCELED", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shipments")
    tracking_number = models.CharField(max_length=20, unique=True, blank=True)
    origin_address = models.TextField(max_length=255)
    destination_address = models.TextField(max_length=255)
    weight = models.DecimalField(max_digits=6, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_delivered(self):
        self.status ='DELIVERED'
        self.save()

    def mark_in_transit(self):
        self.status = 'IN_TRANSIT'
        self.save()

    def save(self, *args, **kwargs):
        # generating tracking_number for shipment
        if not self.tracking_number:
            while True:
                code = str(uuid.uuid4())[:12].upper()
                if not Shipment.objects.filter(tracking_number=code).exists():
                    self.tracking_number = code
                    break

        # calculation for cost of shipment
        self.cost = float(self.weight) * 0.01
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_number} - {self.status}"
    
    def payment_status(self):
        return self.payments.status