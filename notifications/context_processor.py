from .models import Notification


def notifications_count(request):
    """
      Context processor to add unread notification count and recent notifications for the notification dropdown.
    """

    if not request.user.is_authenticated:  # if user is not authenticated an empty dictionary is returned
        return {}

    unread_count = Notification.objects.filter(recipient=request.user,
                                               is_read=False).count()  # retrieves the number of notifications that are unread
    recent = Notification.objects.filter(recipient=request.user)[
             :6]  # retrieves most recent 6 notifications to display on the dropdown

    return {
        "unread_notification_count": unread_count,
        "recent_notifications": recent}  # dictionary returned;
