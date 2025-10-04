"""
defining models for the delivery app to model entities that are to be stored in the database.
"""

from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
from shipments.models import Shipment


class Courier(models.Model):
    """defines model for the Courier entity."""
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name="courier")  # user field related to the django built in User model
    phone = models.CharField(max_length=15)  # phone field for user telephone number.
    vehicle = models.CharField(max_length=50, blank=True, null=True)  # vehicle field for vehicle details
    active = models.BooleanField(default=True)  # active boolean field

    def __str__(self):
        return f"{self.user.username}"


class DeliveryAssignment(models.Model):
    """defines model for the DeliveryAssignment entity(details for a shipment assigned to a courier)"""

    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('ACCEPTED', 'Accepted'),
        ('DELIVERED', 'Delivered'),
    ]
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE,
                                    related_name="deliveryassignment")  # shipment field related to the Shipment model
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE)  # courier field related to the Courier model
    assigned_at = models.DateTimeField(auto_now_add=True)  # data shipment was assigned
    delivered_at = models.DateTimeField(blank=True, null=True)  # date shipment was delivered
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='ASSIGNED')  # status field for status of the delivery

    def mark_accepted(self):
        """sets value of status field to 'accepted' """
        self.status = "ACCEPTED"
        self.save()

    def mark_delivered(self):
        """sets value of status field to 'delivered' """
        self.status = "DELIVERED"
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])

    def __str__(self):
        return f"{self.shipment.tracking_number} -> {self.courier.user.username}"


class CourierApplication(models.Model):
    """defines model for the CourierApplication entity"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)  # user field related to the django built in User model
    phone = models.CharField(max_length=20)  # phone field for user telephone number
    address = models.TextField(max_length=255)  # address field
    vehicle = models.CharField(max_length=50, blank=True, null=True)  # vehicle field for vehicle details
    experience = models.TextField(blank=True, null=True)  # experience field
    is_approved = models.BooleanField(default=False)  # is_approved booleanfield
    created_at = models.DateTimeField(auto_now_add=True)  # date applied

    def __str__(self):
        return f"Application from {self.user.username}"
