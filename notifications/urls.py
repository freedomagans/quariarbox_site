from django.urls import path
from .views import *

app_name = "notifications"  # app name

# list of urls
urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),  # notification list page
    path("mark-read/<int:pk>/", mark_as_read, name="mark_as_read"),  # mark as read url for appropriate view
    path("mark-all-read", mark_all_read, name="mark_all_read"),  # url for bulk(mark as read)
    path("delete/<int:pk>/", delete_notification, name="delete"),  # url for delete view
    path("delete_all", delete_all_notifications, name="delete_all")  # url for bulk delete of notifications
]
