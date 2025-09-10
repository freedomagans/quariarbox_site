from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from shipments.models import Shipment
from delivery.models import DeliveryAssignment, CourierApplication
from users.models import Profile
from .models import Notification
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


# 🔔 shipment created 
@receiver(post_save, sender=Shipment)
def notify_shipment_created(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.user,
            message=f"Shipment {instance.tracking_number} created successfully.",
            link= reverse("shipments:detail", kwargs={"pk": instance.id})
        )

# 🔔 shipment deleted
@receiver(post_delete, sender=Shipment)
def notify_shipment_deleted(sender, instance, **kwargs):
    Notification.objects.create(
        recipient=instance.user,
        message= f"Shipment {instance.tracking_number} has been deleted successfully"
    )

# 🔔 Courier accepted shipment
@receiver(post_save, sender=DeliveryAssignment)
def notifiy_courier_accepted(sender, instance, **kwargs):
    if instance.status == "ACCEPTED":
            Notification.objects.create(
                 recipient=instance.shipment.user,
                 message=f"Shipment {instance.shipment.tracking_number} is In Transit",
                 link= reverse("shipments:detail", kwargs={"pk": instance.shipment.id})
            )

# 🔔 Shipment delivered 
@receiver(post_save, sender=Shipment)
def notify_shipment_delivered(sender, instance, **kwargs):
     if instance.status == "DELIVERED":
          Notification.objects.create(
               recipient=instance.user,
               message=f"Shipment {instance.tracking_number} has been Delivered ✔",
               link= reverse("shipments:detail", kwargs={"pk": instance.id})
          )

# 🔔 Courier application approved
@receiver(post_save, sender=CourierApplication)
def notify_courier_application(sender, instance, **kwargs):
     if instance.is_approved:
          Notification.objects.create(
               recipient=instance.user,
               message="Your courier application has been approved."
          )

# 🔔 Shipment assigned to courier
@receiver(post_save, sender=DeliveryAssignment)
def notify_shipment_assigned(sender, instance, created, **kwargs):
     if created:
          Notification.objects.create(
               recipient=instance.shipment.user,
               message=f"Hello {instance.shipment.user.username} you have been assigned shipment {instance.shipment.tracking_number}.",
               link= reverse("shipments:detail", kwargs={"pk": instance.shipment.id})
          )

# 🔔 A user applys to be a Courier
@receiver(post_save,sender=CourierApplication)
def notify_admin_courierapplication(sender, instance,created, **kwargs):
     if created:
          admins = User.objects.filter(is_superuser=True)

          for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"New courier application received from {instance.user.username}",
                link=reverse("admin:delivery_courierapplication_change", args=[instance.pk])
            )