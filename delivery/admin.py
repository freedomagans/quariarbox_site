"""customising config for admin for the delivery app"""

from django.contrib import admin  # django's admin class
from .models import Courier, DeliveryAssignment, CourierApplication


class CourierAdmin(admin.ModelAdmin):
    """defines admin config for the Courier model."""
    list_display = ('user', 'phone', 'active')  # fields to display


class CourierApplicationAdmin(admin.ModelAdmin):
    """defines admin config for the CourierApplication model"""
    list_display = ('user', 'is_approved')  # fields to display


class DeliveryAssignmentAdmin(admin.ModelAdmin):
    """defines admin config for the DeliveryAssignment model"""
    list_display = ('shipment', 'courier', 'status')  # fields to display

    def get_changeform_initial_data(self, request):
        """ 
        returns initial data to use for forms on the add page of admin for the DeliveryAssignment model
        """
        initial = super().get_changeform_initial_data(request)
        shipment_id = request.GET.get(
            "shipment")  # retrieving shipment id passed into url from the shipment list page in the admin panel
        if shipment_id:
            initial["shipment"] = shipment_id  # setting the value from the url to the shipment entry on the form.
        return initial


# registering Courier,DeliveryAssignment and CourierApplication to admin
admin.site.register(Courier, CourierAdmin)
admin.site.register(DeliveryAssignment, DeliveryAssignmentAdmin)
admin.site.register(CourierApplication, CourierApplicationAdmin)
