from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse

from shipments.models import Shipment
from .models import Notification

# Create your views here.

class NotificationListView(LoginRequiredMixin, ListView):
    login_url= "users:login"
    model = Notification
    template_name = "notifications/list.html"
    context_object_name = "notifications"
    paginate_by = 25

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user).order_by("-created_at")
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_count"] = Notification.objects.filter(recipient=self.request.user, is_read=False).count()
        return context
    
@login_required(login_url="users:login")
def mark_as_read(request, pk):
    """
    Mark a single notification as read. 
    If notification has a link field, redirect to it
    """

    notification = get_object_or_404(Notification, pk=pk,recipient=request.user)

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    redirect_url = getattr(notification, "link", None) or reverse("notifications:list")
    return redirect(redirect_url)

@login_required(login_url="users:login")
@require_POST
def mark_all_read(request):
    """
    Mark all unread notifications for current user as read
     """
    
    Notification.objects.filter(recipient=request.user).update(is_read=True)
    return redirect("notifications:list")


@login_required(login_url="users:login")
def delete_notification(request, pk):
    """Allow user to delete a single notification."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    return redirect(reverse("notifications:list"))