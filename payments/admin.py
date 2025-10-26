"""
defining customised config for django's admin panel for the payments app
"""

from django.contrib import admin  # django's admin class
from .models import Payment, Receipt


class PaymentAdmin(admin.ModelAdmin):
    """
    customises config for the Payment model in django's admin panel
    """

    list_display = (
        "shipment", "user", "amount", "status", "transaction_id", "tx_ref", "created_at")  # fields to display
    list_filter = ("status", "created_at", "method")  # fields to filter by
    search_fields = ("transaction_id", "tx_ref", "user__username", "shipment__tracking_number")  # fields to search by

    readonly_fields = [f.name for f in Payment._meta.fields]  # Make all fields read-only

    def has_add_permission(self, request):
        """ Disables adding new Payment entries manually """
        return False

    def has_delete_permission(self, request, obj=None):
        """ Disable deleting Payments """
        return True


class ReceiptAdmin(admin.ModelAdmin):
    """
    customises config for the Receipt model in django's admin panel
    """

    list_display = ("receipt_number", "payment", "issued_at")  # fields to display
    readonly_fields = [f.name for f in Receipt._meta.fields]  # make all fields read-only

    def has_add_permission(self, request):
        """Disables adding new receipts manually"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disables deleting receipts """
        return True


# registering Payment and Receipt model to django's admin panel
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Receipt, ReceiptAdmin)
