"""
defining customised admin configs 
"""

from django.contrib import admin  # django's admin class
from .models import Shipment
from django.urls import reverse
from django.utils.html import format_html


# Register your models here.
class ShipmentAdmin(admin.ModelAdmin):
    """
    defines customised configs for the Shipment Model in the admin panel
    """
    list_display = (
    "tracking_number", "user", "status", "created_at", "payment_status_badge", "assign_button")  # fields to display
    list_filter = ("status", "created_at", "payment__status")  # fields to filter by
    search_fields = ("tracking_number", "origin_address", "destination_address",)  # fields to search by
    exclude = ("tracking_number", "cost")  # fields to exclude

    def payment_status_badge(self, obj):
        """
        Show payment status with color-coded badges.(customised field)
        and checks status of payment for the shipment and inserts color-coded badges accordingly using the 'formt_html' method
        """

        if hasattr(obj, "payment"):
            status = obj.payment.status
            if status == "PAID":
                return format_html(
                    '<span style="color: white; background: green; padding: 3px 8px; border-radius: 4px;">Paid</span>')
            elif status == "FAILED":
                return format_html(
                    '<span style="color: white; background: red; padding: 3px 8px; border-radius: 4px;">Failed</span>')
            elif status == "PENDING":
                return format_html(
                    '<span style="color: black; background: #f1c40f; padding: 3px 8px; border-radius: 4px;">Pending</span>')
        return "—"

    payment_status_badge.short_description = "Payment Status"  # label to display on table

    def assign_button(self, obj):
        """
        customised display of the assigned button on the assign column for paid shipments
        """

        # case 1: already assigned-> show badge
        if hasattr(obj, 'deliveryassignment'):
            return format_html("<span style='color:blue;padding:3px 8px;border-radius:4px;'>Assigned</span>")

        # case 2: paid but not assigned -> show button 
        elif obj.payment.status == "PAID":
            url = (
                    reverse("admin:delivery_deliveryassignment_add") + f"?shipment={obj.pk}"
            )
            return format_html("<a class='btn-sm btn-primary pt-1 pb-1' style='color:white;' href='{}'>Assign</a>", url)

        # Case 3: Not paid => show nothing 
        return "--"

    assign_button.short_description = "Assignment"  # label to display in table


admin.site.register(Shipment, ShipmentAdmin)  # registering the Shipment model and the customisation class to the admin
