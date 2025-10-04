"""
defining forms for the user app
"""

from django import forms  # django main form class
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.password_validation import validate_password


class UserRegistrationForm(forms.ModelForm):
    """
    Defining a form for UserRegistration : will be display on the register page
    """

    password = forms.CharField(widget=forms.PasswordInput, help_text="Enter a strong password 8 characters long.")  # field for password
    confirm_password = forms.CharField(widget=forms.PasswordInput)  # field for confirm password

    class Meta:  # its used to configure the form
        model = User  # binds form to the User model
        fields = ["username", "email", "password"]  # properties of model to show as fields of the form

    def clean_email(self):
        """
        checks if email is already in the database
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_password(self):
        """implements django validation of password"""
        password = self.cleaned_data.get('password')  # retrieves password
        validate_password(password)  # validates password
        return password

    def clean(self):
        """
        checks if the values in the password field and the confirm_password field of the form match.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        """
        Hashes the password befroe saving so it can be saved to the database 
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data.get("password"))  # set_password() hashes the password value
        if commit:
            user.save()
        return user


class UsersLoginForm(forms.Form):
    """
    defining a form for the login page 
    """
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))


class UserUpdateForm(forms.ModelForm):
    """
    defining a form for the Update user page 
    """

    class Meta:
        model = User  # binds the form to the User model
        fields = ['username', 'first_name', 'last_name', 'email', ]


class ProfileUpdateForm(forms.ModelForm):
    """
    defining a form for the profile update page 
    """

    class Meta:
        model = Profile  # binds the form to the Profile model
        fields = ['profile_pic', 'address', 'phone']
        widgets = {
            'profile_pic': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }),
            'phone': forms.TextInput(
                attrs={'class': 'form-control',
                       'placeholder': 'Enter phone number'
                       }),
            'address': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter your address',
                    'rows': 3
                }),

        }
