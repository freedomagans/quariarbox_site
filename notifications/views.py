""" defining views(processes requests and returns appropriate responses for the notifications app)"""

from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from shipments.models import Shipment
from .models import Notification


# Create your views here.

class NotificationListView(LoginRequiredMixin, ListView):
    """
    processes requests for the nofication list page 
    """
    login_url = "users:login"  # login page if not authenticated
    model = Notification  # binds model to view
    template_name = "notifications/list.html"  # template to render
    context_object_name = "notifications"  # context reference for template
    paginate_by = 25  # num to paginate list by

    def get_queryset(self):
        """ returns list of notifications for user """
        qs = Notification.objects.filter(recipient=self.request.user).order_by("-created_at")
        return qs

    def get_context_data(self, **kwargs):
        """process the context data for template reference """
        context = super().get_context_data(**kwargs)
        context["unread_count"] = Notification.objects.filter(recipient=self.request.user, is_read=False).count()  # context reference for num of unread notifications
        return context


@login_required(login_url="users:login")  # login page if not authenticated(decorator used for FBV)
def mark_as_read(request, pk):
    """
    Mark a single notification as read. 
    If notification has a link field, redirect to it
    """

    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    redirect_url = getattr(notification, "link", None) or reverse(
        "notifications:list")  # redirect url is either the link in the notification instance or list of notifications page
    return redirect(redirect_url)


@login_required(login_url="users:login")  # login page if not authenticated(decorators used)
def mark_all_read(request):
    """
    Mark all unread notifications for current user as read
     """

    Notification.objects.filter(recipient=request.user).update(
        is_read=True)  # updates the is_read field of filtered notifications to True.
    return redirect("notifications:list")  # redirect to notifications list page


@login_required(login_url="users:login")  # login page if not authenticated (decorators used)
def delete_notification(request, pk):
    """Allow user to delete a single notification."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    messages.warning(request, "Nofication has been deleted.")
    return redirect(reverse("notifications:list"))


@login_required(login_url="users:login")  # login page if not authenticated(decorators used)
def delete_all_notifications(request):
    """Allow user to delete all notifications."""
    Notification.objects.filter(recipient=request.user).delete()
    messages.warning(request, "Notifications deleted.")
    return redirect("notifications:list")
