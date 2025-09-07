from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView
from django.views.generic.edit import FormView
from .forms import UserRegistrationForm, UsersLoginForm, UserUpdateForm, ProfileUpdateForm


# Create your views here.
class RegisterView(FormView):
    template_name = "users/register.html"  # template to render
    form_class = UserRegistrationForm  # the form for this view
    success_url = reverse_lazy("users:login")  # page to load after successful validation "/users/login"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class LoginView(FormView):
    template_name = "users/login.html"
    form_class = UsersLoginForm
   
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy("home")
       

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]

        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)  # redirects to success_url
        else:
            form.add_error(None, "Invalid username or password")
            return self.form_invalid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)  # ends the session
        return redirect("home")


class ProfileView(LoginRequiredMixin, UpdateView):
    login_url = "users:login"
    model = User
    form_class = UserUpdateForm
    template_name = "users/profile.html"
    context_object_name = "user"

    def get_object(self, queryset= None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["user_form"] = UserUpdateForm(self.request.POST, instance=self.request.user)
            context["profile_form"] = ProfileUpdateForm(self.request.POST,self.request.FILES, instance=self.request.user.profile)
        else:
            context["user_form"] = UserUpdateForm(instance=self.request.user)
            context["profile_form"] = ProfileUpdateForm(instance=self.request.user.profile)
        return context
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context["user_form"]
        profile_form = context["profile_form"]

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("users:profile")
        else:
            return self.render_to_response(self.get_context_data(form=form))