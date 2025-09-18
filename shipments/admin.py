from django.contrib import admin
from .models import Shipment
from django.urls import reverse
from django.utils.html import format_html

# Register your models here.
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("tracking_number", "user", "status", "created_at","payment_status", "assign_button")
    list_filter = ("status", "created_at")
    search_fields = ("tracking_number", "origin_address", "destination_address",)
    exclude = ("tracking_number","cost")

    def assign_button(self,obj):
        #case 1: already assigned-> show badge
        if hasattr(obj, 'deliveryassignment'):
            return format_html("<span style='color:blue;padding:3px 8px;border-radius:4px;'>Assigned</span>")
        
        # case 2: paid but not assigned -> show button 
        elif obj.payments.status== "PAID":
                url = (
                    reverse("admin:delivery_deliveryassignment_add") + f"?shipment={obj.pk}"
                )
                return format_html("<a class='btn btn-primary pt-1 pb-1' style='color:white;' href='{}'>Assign</a>", url)
            
        # Case 3: Not paid => show nothing 
        return "--"


    assign_button.short_description = "Assignment"
    assign_button.allow_tags = True


admin.site.register(Shipment, ShipmentAdmin)
