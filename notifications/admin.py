from django.contrib import admin  # django's admin class
from .models import Notification

admin.site.register(Notification)  # registers the Notification Model
