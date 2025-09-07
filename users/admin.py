from django.contrib import admin
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')


# Register your models here.
admin.site.register(Profile, ProfileAdmin)


#customised tweaks for admin 
admin.site.site_header = "Quariarbox Administration"
admin.site.site_title = "Quariarbox"
admin.site.index_title = "Welcome to Quariarbox "


