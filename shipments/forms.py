from django import forms
from .models import Shipment


class ShipmentForm(forms.ModelForm):
    """
    defining a form for the create shipment page
    """

    class Meta:
        model = Shipment  # binds form to the Shipment model
        exclude = ['user', 'tracking_number', 'status', 'cost']  # excludes specified fields
