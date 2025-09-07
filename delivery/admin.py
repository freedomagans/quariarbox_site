from django.contrib import admin
from .models import Courier, DeliveryAssignment, CourierApplication


# Register your models here.
class CourierAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'active')

class CourierApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved')

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'status')

admin.site.register(Courier, CourierAdmin)
admin.site.register(DeliveryAssignment, DeliveryAdmin)
admin.site.register(CourierApplication, CourierApplicationAdmin)
