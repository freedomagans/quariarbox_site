from .models import Notification

def notifications_count(request):
    """
      Context processor to add unread notification count and recent notifications
    (for quick navbar dropdown display).
    """

    if not request.user.is_authenticated:
        return {}
    
    unread_count = Notification.objects.filter(recipient=request.user,is_read=False).count()
    recent = Notification.objects.filter(recipient=request.user)[:6]

    return {
        "unread_notification_count": unread_count,
        "recent_notifications": recent}