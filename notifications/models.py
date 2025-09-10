from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Notification(models.Model):
    recipient = models.ForeignKey(User,on_delete=models.CASCADE,related_name="notifications")
    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    
    def mark_as_read(self):
        self.is_read = True
        self.save()


    def __str__(self):
        return f"To {self.recipient.username}: {self.message[:50]}"