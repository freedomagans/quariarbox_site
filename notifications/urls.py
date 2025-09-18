from django.urls import path
from .views import *

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path("mark-read/<int:pk>/", mark_as_read, name="mark_as_read"),
    path("mark-all-read", mark_all_read, name="mark_all_read"),
    path("delete/<int:pk>/", delete_notification, name="delete"),
    path("delete_all", delete_all_notifications,name="delete_all" )
]
