from django import forms
from django.contrib.auth.models import User
from .models import Profile


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    # Validation to ensure password match
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash the password befroe saving
        user.set_password(self.cleaned_data.get("password"))
        if commit:
            user.save()
        return user


class UsersLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields= ['username','first_name', 'last_name', 'email',]

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic', 'address', 'phone']
        widgets = {
              'profile_pic':forms.FileInput(
            attrs={
                    'class':'form-control',
                    'accept': 'image/*'
                }),
            'phone':forms.TextInput(
            attrs={'class':'form-control',
                   'placeholder':'Enter phone number'
                   }),
            'address':forms.Textarea(
            attrs={
                       'class': 'form-control',
                       'placeholder': 'Enter your address',
                       'rows': 3
                   }),
          
                   }