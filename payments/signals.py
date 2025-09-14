from django.db.models.signals import post_save
from django.dispatch import receiver
from shipments.models import Shipment
from .models import Payment
from notifications.models import Notification 
from django.urls import reverse
from django.contrib.auth.models import User


#=========Notification for users=============
@receiver(post_save,sender=Shipment)
def create_payment_for_shipment(sender,instance,created, **kwargs):
    if created and not hasattr(instance, "payments"):
        Payment.objects.create(user=instance.user, shipment=instance, amount=instance.cost)

@receiver(post_save, sender=Payment)
def on_payment_processing(sender,instance,**kwargs):
    if instance.status == 'PAID':

        #User notification
        Notification.objects.create(
            recipient=instance.user,
            message=f"Payment for shipment {instance.shipment.tracking_number} was successful ",
            link=reverse("shipments:detail",kwargs={"pk":instance.shipment.id})
        )

        #admin notification
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"customer has paid for shipment {instance.shipment.tracking_number} and is ready for courier assignment",
                link=reverse("admin:shipments_shipment_changelist")
            )

    if instance.status == "FAILED":
        Notification.objects.create(
            recipient=instance.user,
            message=f"Payment for shipment {instance.shipment.tracking_number} Failed!!", 
            link=reverse("shipments:detail", kwargs={"pk":instance.shipment.id})
        )

#=========Notification for admins===========
