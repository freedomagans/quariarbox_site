from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("courier", "Courier"),
        ("admin", "Admin"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    #Profile picture field
    profile_pic = models.ImageField(upload_to="profile_pics/", default="profile_pics/default.png", blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}({self.role})"
