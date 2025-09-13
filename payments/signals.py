from django.db.models.signals import post_save
from django.dispatch import receiver
from shipments.models import Shipment
from .models import Payment

@receiver(post_save,sender=Shipment)
def create_payment_for_shipment(sender,instance,created, **kwargs):
    if created and not hasattr(instance, "payments"):
        Payment.objects.create(user=instance.user, shipment=instance, amount=instance.cost)