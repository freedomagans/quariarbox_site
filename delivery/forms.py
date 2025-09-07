from django import forms
from .models import CourierApplication

class CourierApplicationForm(forms.ModelForm):
    class Meta:
        model = CourierApplication
        exclude = ['user', 'is_approved']

        