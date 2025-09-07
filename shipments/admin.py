from django.contrib import admin
from .models import Shipment


# Register your models here.
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("tracking_number", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tracking_number", "origin_address", "destination_address")
    exclude = ("tracking_number",)


admin.site.register(Shipment, ShipmentAdmin)
