from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Courier, CourierApplication
from users.models import Profile

@receiver(post_save, sender=Courier)
def set_user_role_to_courier(sender, instance, created, **kwargs):
    if created:
        profile = instance.user.profile
        profile.role = "courier"
        profile.save()

@receiver(post_save, sender=CourierApplication)
def create_courier_on_approval(sender, instance, created, **kwargs):
    if not created and instance.is_approved:
        courier_exists = Courier.objects.filter(user=instance.user).exists()
        if not courier_exists:
            Courier.objects.create(user=instance.user, phone=instance.phone,  vehicle=instance.vehicle)
    
    else:
        try:
            Courier.objects.get(user=instance.user).delete()
        except Courier.DoesNotExist:
            pass
