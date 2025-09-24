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



#=========Notification for users=============
@receiver(post_save,sender=Shipment)
def create_payment_for_shipment(sender,instance,created, **kwargs):

    instance.calc_cost()

    if created:
        Payment.objects.create(user=instance.user, shipment=instance, amount=instance.cost)

    else:
        try:
            payment = Payment.objects.get(user=instance.user, shipment=instance)
            payment.amount = instance.cost
            payment.save()
        except Payment.DoesNotExist:
            pass


@receiver(post_save, sender=Payment)
def on_payment_processing(sender,instance,**kwargs):
    if instance.status == 'PAID':

        #User notification
        Notification.objects.create(
            recipient=instance.user,
            message=f"Payment was successful click to view receipt",
            link=reverse("payments:receipt",kwargs={"shipment_id":instance.shipment.id})
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


@receiver(post_save, sender=Payment)
def send_payment_success_email(sender, instance, created, **kwargs):
    """
    Send a styled email to user when a payment is marked as PAID
    """

    if instance.status == "PAID":
        user = instance.user
        shipment = instance.shipment

        #Absolute URL for shipment detail
        shipment_url = settings.SITE_URL + reverse("shipments:detail", args=[shipment.pk])

        # Render HTML + plain text 
        context = {
            "user": user, 
            "shipment": shipment,
            "payment": instance,
            "shipment_url": shipment_url,
        }

        subject = f"Payment Confirmation - Shipment {shipment.tracking_number}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [user.email]
        html_content = render_to_string("emails/payment_success.html", context)
        text_content = render_to_string("emails/payment_success.txt", context)

        msg = EmailMultiAlternatives(subject, text_content,from_email,to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        