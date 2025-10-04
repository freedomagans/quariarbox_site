"""
defining views(process requests and returns appropriate responses) for the delivery app
"""

from django.http import HttpResponseNotFound
from django.views.generic import CreateView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import CourierApplication, DeliveryAssignment, Courier
from .forms import CourierApplicationForm
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from shipments.models import Shipment
from django.contrib.auth.decorators import login_required
from django.db import models
from notifications.models import Notification


# Create your views here.
class CourierApplicationView(LoginRequiredMixin, CreateView):
    """
    processes request for the courier application page
    """
    login_url = "users:login"  # login page if not authenticated
    model = CourierApplication  # binds model to this view
    template_name = "delivery/create.html"  # template to render
    form_class = CourierApplicationForm  # binds form to this view
    success_url = reverse_lazy("delivery:success")  # url to redirect on successful validation of form

    def dispatch(self, request, *args, **kwargs):
        """
        handles redirects base on if courier objects already exists or user has already applied.
        """
        # ✅ If user is already an approved courier
        if Courier.objects.filter(user=request.user).exists():  # checks if courier object already exists
            return redirect("delivery:list")  # redirects to list of assigned deliveries page

        # ✅ If user already submitted an application
        if CourierApplication.objects.filter(user=request.user).exists():
            messages.warning(self.request,
                             "You have already submitted a courier application. Please wait for admin approval.")  # sends messaged to displayed page
            return redirect("home")  # redirects to home page

        # ✅ Otherwise allow normal form flow
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """validates form entries"""

        form.instance.user = self.request.user  # sets value for user field of instance(CourierApplication) to the authenticated user

        messages.info(self.request,
                      "Your application has been submitted. Please wait for approval.")  # sends message to displayed page

        # ✅ Notify user on successful application submission
        Notification.objects.create(
            recipient=self.request.user,
            message="Your courier application has been submitted successfully. An admin will review it soon.",
            link="delivery:success"
        )

        return super().form_valid(form)


class CourierListView(LoginRequiredMixin, ListView):
    """
    process requests for assigned deliveries page
    """

    login_url = "users:login"  # login page if not authenticated
    template_name = "delivery/list.html"  # template to render
    context_object_name = "assigned_deliveries"  # context reference for the returned queryset

    def dispatch(self, request, *args, **kwargs):
        """
        checks if courier object already exist for user if not if then checks if user has applied to be a courier if not it then sends them to application page 
        """
        try:
            courier = Courier.objects.get(user=request.user)  # gets courier object if exists
        except Courier.DoesNotExist:  # if not exist
            if CourierApplication.objects.filter(user=request.user):  # checks if user applied
                return redirect("delivery:success")  # redirect to successful application page
            return redirect("delivery:create")  # if not applied redirects to application page
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        returns queryset that'll be referenced in the template as the context_object
        """

        user = self.request.user  # user
        query = self.request.GET.get("q")  # search parameter 'q' for searching shipment list
        status = self.request.GET.get("status")  # status parameter for filetering shipment list

        qs = DeliveryAssignment.objects.filter(courier=user.courier).order_by(
            "-assigned_at")  # retrieves assigned shipments for the user

        if query:
            qs = qs.filter(
                models.Q(shipment__tracking_number__icontains=query) |
                models.Q(shipment__origin_address__icontains=query) |
                models.Q(shipment__destination_address__icontains=query)
            )  # filters assigned shipments list based on search parameter

        if status and status != "ALL":
            qs = qs.filter(status=status)  # filters assigned shipments list based on status parameter

        return qs  # returns final queryset(assigned shipments)

    def get_context_data(self, **kwargs):
        """
        sets and returns context data to be referenced in the template 
        """
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Shipment.STATUS_CHOICES  # sets context reference for status choices
        context["selected_status"] = self.request.GET.get("status",
                                                          "ALL")  # sets context reference for selected_status
        context["query"] = self.request.GET.get("q", "")  # sets context reference for query search parameter
        return context


class SuccessView(LoginRequiredMixin, TemplateView):
    """process the request for the application success page"""
    template_name = "delivery/application_success.html"  # template to render
    login_url = "users:login"  # login page if not authenticated


@login_required(login_url="users:login")  # login page if not authenticated(decorators used)
def accept_delivery_view(request, id):
    """
    process the request for accepting deliveries
    """
    
    accepted_shipment = Shipment.objects.get(id=id)  # retrieves the assigned shipment
    delivery_assignment_for_this_shipment = DeliveryAssignment.objects.get(
        shipment=accepted_shipment)  # retrieves the deliveryassignment for the assigned shipment
    
    if delivery_assignment_for_this_shipment.courier.user == request.user:
        accepted_shipment.mark_in_transit()  # sets the status for the shipment to in transit.
        delivery_assignment_for_this_shipment.mark_accepted()  # sets the status for the delivery_assignmet object to accepted.
        messages.info(request,
                    f"Shipment {accepted_shipment.tracking_number} accepted and ready for delivery")  # sends message to displayed page
        return redirect("delivery:list")  # redirects to list of assigned shipments.
    else:
        return HttpResponseNotFound(request)


@login_required(login_url="users:login")  # login page if not authenticated
def delivered_delivery_view(request, id):
    """
    process the request for delivering assigned shipment
    """
    delivered_shipment = get_object_or_404(Shipment, id=id)  # retrieves shipment
    assignment = DeliveryAssignment.objects.get(
        shipment=delivered_shipment)  # retrieves the deliveryAssignment for the shipment
    if assignment.courier.user == request.user:
        if assignment.status != 'ACCEPTED':
            return redirect("delivery:list")
        
        delivered_shipment.mark_delivered()  # sets the status of the shipment to delivered
        assignment.mark_delivered()  # sets the status of the delivery assignment to delivered.
        messages.success(request,
                        "Shipment marked as delivered successfully.")  # sends success message to the displayed page
        return redirect("delivery:list")  # redirects to list of assigned shipments page
    else:
        return HttpResponseNotFound(request)
