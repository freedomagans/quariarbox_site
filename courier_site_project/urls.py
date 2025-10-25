"""
URL configuration for courier_site_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from .views import home,custom_admin_logout

urlpatterns = [
    path('',home, name="home"),
    path('secure-admin-panel/', admin.site.urls, name='admin'),
    path("admin/logout/", custom_admin_logout, name="admin-logout"),
    path('users/', include("users.urls")),
    path('shipments/', include("shipments.urls")),
    path("delivery/", include("delivery.urls")),
    path("notifications/", include("notifications.urls")),
    path("payments/", include("payments.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
