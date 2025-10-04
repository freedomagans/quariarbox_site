"""
Defining views(processes requests and returns the necessary responses)
"""

from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView
from django.views.generic.edit import FormView
from .forms import UserRegistrationForm, UsersLoginForm, UserUpdateForm, ProfileUpdateForm


class RegisterView(FormView):
    """
    processes request for the register page 
    """
    template_name = "users/register.html"  # template to render
    form_class = UserRegistrationForm  # the form for this view
    success_url = reverse_lazy("users:login")  # page to load after successful validation "/users/login"

    def form_valid(self, form):
        """
        if form is valid it saves form data into the database
        """
        form.save()
        messages.success(self.request,
                         "congrats your account is registered successfully.")  # sends a success message to the displayed page
        return super().form_valid(form)


class LoginView(FormView):
    """
    process requests for the login page
    """
    template_name = "users/login.html"  # template to render
    form_class = UsersLoginForm  # form for this view

    def dispatch(self, request, *args, **kwargs):
        """redirects users to home page if they are already logged in"""
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy("home"))  # redirecting to home page if authenticated
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """
        reroutes to the value of the 'next' value if specified in url but 
        if not it sends user to home page
        """
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy("home")

    def form_valid(self, form):
        """
        if form valid it gets the login values and authenticates the user

        """
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(self.request, username=username,
                            password=password)  # authenticate method of the auth class in django user to
        # authenticate entries
        if user is not None:
            login(self.request, user)  # creates a session with authenticated user
            messages.success(self.request,
                             f" Welcome {self.request.user.username} you are logged in.")  # sends a success message to the displayed page
            return super().form_valid(form)  # redirects to success_url
        else:
            form.add_error(None,
                           "Invalid username or password")  # displays error if user is not authenticated successfully
            return self.form_invalid(form)


class LogoutView(View):
    """
    processes the logout logic
    """

    def get(self, request):
        logout(request)  # ends the session for the user
        messages.error(self.request, "Bye! you have been logged out.")  # sends a message to the displayed page
        return redirect("home")  # redirects to home page


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    processes requests for the Profile page
    """
    login_url = "users:login"  # page to route to if not authenticated.
    model = User  # model for this CBV(class based view)
    form_class = UserUpdateForm  # form for this view
    template_name = "users/profile.html"  # template to render
    context_object_name = "user"  # the reference to the return object in the template

    def get_object(self, queryset=None):
        """
        returns the object to be referenced (updated) by the view
        """
        return self.request.user

    def get_context_data(self, **kwargs):
        """
        processes the context dictionary that gets referenced in the template
        """
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["user_form"] = UserUpdateForm(self.request.POST,
                                                  instance=self.request.user)  # setting context reference for the user update form on the context dictionary when the entries are updated
            context["profile_form"] = ProfileUpdateForm(self.request.POST, self.request.FILES,
                                                        instance=self.request.user.profile)  # setting context reference for the user profile update form on the context dictionary when the entries are updated
        else:
            context["user_form"] = UserUpdateForm(instance=self.request.user)  # context reference for user update form
            context["profile_form"] = ProfileUpdateForm(
                instance=self.request.user.profile)  # context reference for profile update form
        return context

    def form_valid(self, form):
        """
        validates form and saves the entries to the database
        """
        context = self.get_context_data()
        user_form = context["user_form"]
        profile_form = context["profile_form"]

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(self.request,
                             "Profile updated successfully.")  # sends success message to the displayed page
            return redirect("users:profile")  # reloads the profile page
        else:
            return self.render_to_response(
                self.get_context_data(form=form))  # renders template with context data specified
