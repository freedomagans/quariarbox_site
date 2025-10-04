"""
customised admin config:
"""

from django.contrib import admin  # django's admin class
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # the properties that will display as columns


# registering the Profile model on the admin site
admin.site.register(Profile, ProfileAdmin)

# customised tweaks for admin
admin.site.site_header = "Quariarbox Administration"
admin.site.site_title = "Quariarbox"
admin.site.index_title = "Welcome to Quariarbox "
