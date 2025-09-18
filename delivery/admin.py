from django.contrib import admin
from .models import Courier, DeliveryAssignment, CourierApplication


# Register your models here.
class CourierAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'active')

class CourierApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_approved')

class DeliveryAssignmentAdmin(admin.ModelAdmin):
    list_display = ('shipment','courier', 'status')

    def get_changeform_initial_data(self, request):
        initial =  super().get_changeform_initial_data(request)
        shipment_id = request.GET.get("shipment")
        if shipment_id:
            initial["shipment"] = shipment_id
        return initial

admin.site.register(Courier, CourierAdmin)
admin.site.register(DeliveryAssignment, DeliveryAssignmentAdmin)
admin.site.register(CourierApplication, CourierApplicationAdmin)
