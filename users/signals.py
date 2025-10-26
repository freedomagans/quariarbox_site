from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """
    defining signal to kickin when an instance of User model is created.
    """
    if created:
        if instance.is_superuser:
            Profile.objects.create(user=instance, role='admin')
        else:
            Profile.objects.create(user=instance)
        


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """
    defining signal to kickin when an instance of User model is saved.
    """
    instance.profile.save()

