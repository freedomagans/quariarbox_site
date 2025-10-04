"""defining signals for the delivery app"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Courier, CourierApplication
from users.models import Profile
from django.contrib.auth.models import User


# signal to set user role to courier when a new courier object is created for that user
@receiver(post_save, sender=Courier)
def set_user_role_to_courier(sender, instance, created, **kwargs):
    if created:
        profile = instance.user.profile
        profile.role = "courier"
        profile.save()


# signal to create courier object when Courier application is approved
@receiver(post_save, sender=CourierApplication)
def create_courier_on_approval(sender, instance, created, **kwargs):
    if not created and instance.is_approved:
        courier_exists = Courier.objects.filter(
            user=instance.user).exists()  # checks if courier object already exists for user
        if not courier_exists:
            Courier.objects.create(user=instance.user, phone=instance.phone,
                                   vehicle=instance.vehicle)  # creates courier object for the user

    else:
        try:
            """ deletes courier object when is_approved is turned false."""
            Courier.objects.get(user=instance.user).delete()
            instance.user.profile.role = "customer"
            instance.user.profile.save()
        except Courier.DoesNotExist:
            pass
