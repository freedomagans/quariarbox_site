from django.urls import path
from . import views

app_name = "users"  # name for indexing urls when loading url

# list of urls for the user app specified in the urlpatterns list.
urlpatterns = [
    path("", views.RegisterView.as_view(), name="register"),  # register page url
    path("login/", views.LoginView.as_view(), name="login"),  # login page url
    path("logout/", views.LogoutView.as_view(), name="logout"),  # logout url
    path("profile/", views.ProfileView.as_view(), name="profile"),  # profile page url
    path('lockout/', views.AxesLockoutView.as_view(), name='lockout')
]
