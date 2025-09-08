from django.contrib.auth.models import User
from django.db import models
from shipments.models import Shipment



# Create your models here.
class Courier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="courier")
    phone = models.CharField(max_length=15)
    vehicle = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}"


class DeliveryAssignment(models.Model):
    STATUS_CHOICES =[
        ('ASSIGNED', 'Assigned'),
        ('ACCEPTED', 'Accepted'),
        ('DELIVERED','Delivered'),
    ]
    shipment = models.OneToOneField(Shipment, on_delete=models.CASCADE, related_name="shipment")
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,default='ASSIGNED')

    def mark_accepted(self):
        self.status = "ACCEPTED"
        self.save()

    def mark_delivered(self):
        self.status = "DELIVERED"
        self.save()

    def __str__(self):
        return f"{self.shipment.tracking_number} -> {self.courier.user.username}"
    
class CourierApplication(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    address = models.TextField(max_length=255)
    vehicle = models.CharField(max_length=50, blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Application from {self.user.username}"
