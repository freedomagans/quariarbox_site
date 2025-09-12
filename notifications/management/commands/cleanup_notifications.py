from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from notifications.models import Notification


class Command(BaseCommand):
    help = "Delete notifications older than 2 weeks"

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(weeks=2)
        old = Notification.objects.filter(created_at__lt=cutoff)
        count = old.count()
        old.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} old notifications."))
