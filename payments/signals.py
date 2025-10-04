"""defining signals for the payments app"""
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
from shipments.models import Shipment
from .models import Payment
from notifications.models import Notification
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


# signal for creating a pending payment instance(row) on Shipment creation
@receiver(post_save, sender=Shipment)
def create_payment_for_shipment(sender, instance, created, **kwargs):
    instance.calc_cost()  # gets cost for instance

    if created:
        Payment.objects.create(user=instance.user, shipment=instance, amount=instance.cost)

    else:
        try:
            """updates cost value on update of Payment model instance(row)"""
            payment = Payment.objects.get(user=instance.user, shipment=instance)
            payment.amount = instance.cost
            payment.save()
        except Payment.DoesNotExist:
            pass


# =========Notification for users=============

# signal for Notifying user on updating Payment instance status
@receiver(post_save, sender=Payment)
def on_payment_processing(sender, instance, **kwargs):
    if instance.status == 'PAID':
        # Notify User on successful payment
        Notification.objects.create(
            recipient=instance.user,
            message=f"Payment was successful click to view receipt",
            link=reverse("payments:receipt", kwargs={"shipment_id": instance.shipment.id})
        )
        # notify all admins on users sucessful payment
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"customer has paid for shipment {instance.shipment.tracking_number} and is ready for courier assignment",
                link=reverse("admin:shipments_shipment_changelist")
            )

    if instance.status == "FAILED":
        # Notify user on failed payment
        Notification.objects.create(
            recipient=instance.user,
            message=f"Payment for shipment {instance.shipment.tracking_number} Failed!!",
            link=reverse("shipments:detail", kwargs={"pk": instance.shipment.id})
        )


@receiver(post_save, sender=Payment)
def send_payment_success_email(sender, instance, created, **kwargs):
    """
    Send a styled email to user when a payment is marked as PAID
    """

    if instance.status == "PAID":
        user = instance.user
        shipment = instance.shipment

        # Absolute URL for shipment detail
        shipment_url = settings.SITE_URL + reverse("shipments:detail", args=[shipment.pk])

        # Render HTML + plain text 
        context = {
            "user": user,
            "shipment": shipment,
            "payment": instance,
            "shipment_url": shipment_url,
        }  # context for email

        subject = f"Payment Confirmation - Shipment {shipment.tracking_number}"  # subject of email
        from_email = settings.DEFAULT_FROM_EMAIL  # sender email
        to = [user.email]  # email of recipient
        html_content = render_to_string("emails/payment_success.html", context)  # html content for email
        text_content = render_to_string("emails/payment_success.txt", context)  # text string content for email

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)  # used for sending multipart emails
        # (html and text content)
        msg.attach_alternative(html_content, "text/html")  # attaches the html content
        msg.send()  # sends email
