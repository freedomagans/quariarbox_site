from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth import get_user_model
from shipments.models import Shipment
from delivery.models import DeliveryAssignment, CourierApplication
from .models import Notification

User = get_user_model()


# ========== USER NOTIFICATIONS ==========

# Shipment created
@receiver(post_save, sender=Shipment)
def notify_user_shipment_created(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.user,
            message=f"Shipment {instance.tracking_number} created successfully.",
            link=reverse("shipments:detail", kwargs={"pk": instance.pk})
        )


# Shipment deleted
@receiver(post_delete, sender=Shipment)
def notify_user_shipment_deleted(sender, instance, **kwargs):
    Notification.objects.create(
        recipient=instance.user,
        message=f"Shipment {instance.tracking_number} has been deleted successfully"
    )


# Courier accepted shipment
@receiver(post_save, sender=DeliveryAssignment)
def notify_user_courier_accepted(sender, instance, **kwargs):
    if instance.status == "ACCEPTED":
        Notification.objects.create(
            recipient=instance.shipment.user,
            message=f"Shipment {instance.shipment.tracking_number} is In Transit",
            link=reverse("shipments:detail", kwargs={"pk": instance.shipment.pk})
        )


# Shipment delivered
@receiver(post_save, sender=Shipment)
def notify_user_shipment_delivered(sender, instance, **kwargs):
    if instance.status == "DELIVERED":
        Notification.objects.create(
            recipient=instance.user,
            message=f"Shipment {instance.tracking_number} has been Delivered ✔",
            link=reverse("shipments:detail", kwargs={"pk": instance.pk})
        )


# Courier application approved
@receiver(post_save, sender=CourierApplication)
def notify_user_courier_application(sender, instance, **kwargs):
    if instance.is_approved:
        Notification.objects.create(
            recipient=instance.user,
            message="Your courier application has been approved.",
            link=reverse("delivery:list")
        )


# Shipment assigned to courier
@receiver(post_save, sender=DeliveryAssignment)
def notify_courier_assigned(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.courier.user,
            message=f"Hello {instance.courier.user.username}, you have been assigned shipment {instance.shipment.tracking_number}.",
            link=reverse("shipments:detail", kwargs={"pk": instance.shipment.pk})
        )


# ========== ADMIN NOTIFICATIONS ==========

# New courier application
@receiver(post_save, sender=CourierApplication)
def notify_admin_courier_application(sender, instance, created, **kwargs):
    if created:
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"New courier application received from {instance.user.username}",
                link=reverse("admin:delivery_courierapplication_change", args=[instance.pk])
            )


# Courier accepted shipment
@receiver(post_save, sender=DeliveryAssignment)
def notify_admin_courier_accepted(sender, instance, **kwargs):
    if instance.status == "ACCEPTED":
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"Shipment {instance.shipment.tracking_number} delivery was accepted",
                link=reverse("admin:delivery_deliveryassignment_changelist")
            )


# Shipment created
@receiver(post_save, sender=Shipment)
def notify_admin_shipment_created(sender, instance, created, **kwargs):
    if created:
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"Shipment {instance.tracking_number} was created.",
                link=reverse("admin:shipments_shipment_changelist")
            )


# Shipment deleted
@receiver(post_delete, sender=Shipment)
def notify_admin_shipment_deleted(sender, instance, **kwargs):
    admins = User.objects.filter(is_superuser=True)
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            message=f"Shipment {instance.tracking_number} was deleted.",
            link=reverse("admin:shipments_shipment_changelist")
        )


# Shipment delivered
@receiver(post_save, sender=Shipment)
def notify_admin_shipment_delivered(sender, instance, **kwargs):
    if instance.status == "DELIVERED":
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"Shipment {instance.tracking_number} has been Delivered ✔",
                link=reverse("admin:shipments_shipment_changelist")
            )
