"""
defining models for the shipments app to model entities to be stored in the database
"""

from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone


class Shipment(models.Model):
    """
    defining the Model for the Shipment entity
    """
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("IN_TRANSIT", "In Transit"),
        ("DELIVERED", "Delivered"),
        ("CANCELED", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="shipments")  # user field related to the built in django's User model
    tracking_number = models.CharField(max_length=20, unique=True,
                                       blank=True)  # tracking id field to uniquely identify and track shipments
    origin_address = models.TextField(max_length=255)  # origin address field
    destination_address = models.TextField(max_length=255)  # destination address field
    weight = models.DecimalField(max_digits=6, decimal_places=2)  # shipments weight field
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # cost of shipment field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")  # shipments status field
    created_at = models.DateTimeField(auto_now_add=True)  # date created automatically filled on creation
    updated_at = models.DateTimeField(auto_now=True)  # date updated automatically filled on update

    def mark_delivered(self):
        """method to set status to delivered"""
        self.status = 'DELIVERED'
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])

    def mark_in_transit(self):
        """method to set status to in_transit"""
        self.status = 'IN_TRANSIT'
        self.save()

    def calc_cost(self):
        """method to calculate cost of shipment"""
        self.cost = float(self.weight) * 0.01

    def save(self, *args, **kwargs):
        """ 
        overriding save() method to auto generate unique tracking_numbers on saving instances of the shipment 
        """
        # generating tracking_number for shipment
        if not self.tracking_number:
            while True:
                code = str(uuid.uuid4())[:12].upper()  # generating unique tracking_id using uuid
                if not Shipment.objects.filter(tracking_number=code).exists():
                    self.tracking_number = code
                    break

        # calculation for cost of shipment
        self.calc_cost()  # sets cost for shipment
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tracking_number} - {self.status}"

    def payment_status(self):
        """returns status of related payments field"""
        return self.payments.status
