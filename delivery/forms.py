from django import forms
from .models import CourierApplication


class CourierApplicationForm(forms.ModelForm):
    """defines form for the Courier application page """

    class Meta:
        model = CourierApplication  # binds model to form
        exclude = ['user', 'is_approved']  # fields to exclude
