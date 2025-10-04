"""
Defining models for the user app which models entities to store data in database
"""

from django.db import models  # django's model class
from django.contrib.auth.models import User  # django's prebuilt User model


class Profile(models.Model):
    """
    defining a Model for the Profile entity
    """

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("courier", "Courier"),
        ("admin", "Admin"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)  # user field related to django's User Model
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,
                            default="customer")  # role field with preset options for role choices
    phone = models.CharField(max_length=20, blank=True, null=True)  # phone field
    address = models.TextField(blank=True, null=True)  # address field
    profile_pic = models.ImageField(upload_to="profile_pics/", default="profile_pics/default.png", blank=True,
                                    null=True)  # profile picture field with a default photo

    def __str__(self):
        """
        will display when object of self is printed or __str__ is called.
        """
        return f"{self.user.username}({self.role})"
