from django.shortcuts import render, redirect
from django.contrib.auth import logout
def home(request):
    return render(request, "index.html", None)

def custom_admin_logout(request):
    logout(request)
    return redirect("home")