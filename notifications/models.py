"""defining models for the notifications app to model entities to store in the database """
from django.db import models  # django's models class
from django.contrib.auth.models import User  # django's built in User model


class Notification(models.Model):
    """models the Notification entity to be stored in the database"""

    recipient = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name="notifications")  # recipient field related to the built in django User model
    message = models.TextField()  # notification message field
    link = models.URLField(blank=True, null=True)  # link field
    is_read = models.BooleanField(default=False)  # is_read boolean field
    created_at = models.DateTimeField(auto_now_add=True)  # date created

    class Meta:
        ordering = ["-created_at"]  # the order instances(rows) are to be stored

    def mark_as_read(self):
        """sets the is_read field to True."""
        self.is_read = True
        self.save()

    def __str__(self):
        return f"To {self.recipient.username}: {self.message[:50]}"
