from django.views.generic import CreateView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import CourierApplication, DeliveryAssignment, Courier
from .forms import CourierApplicationForm
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from shipments.models import Shipment
from django.contrib.auth.decorators import login_required
from django.db import models
from notifications.models import Notification
# Create your views here.
class CourierApplicationView(LoginRequiredMixin,CreateView):
    login_url = "users:login"
    model = CourierApplication
    template_name = "delivery/create.html"
    form_class = CourierApplicationForm
    success_url = reverse_lazy("delivery:success")

    def dispatch(self, request, *args, **kwargs):
        # ✅ If user is already an approved courier
        if Courier.objects.filter(user=request.user).exists():
            return redirect("delivery:list")

        # ✅ If user already submitted an application
        if CourierApplication.objects.filter(user=request.user).exists():
            Notification.objects.create(
                recipient=request.user,
                message="You have already submitted a courier application. Please wait for admin approval.",
                link="delivery:success"
            )
            return redirect("home")

        # ✅ Otherwise allow normal form flow
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)

        # ✅ Notify user on successful application submission
        Notification.objects.create(
            recipient=self.request.user,
            message="Your courier application has been submitted successfully. An admin will review it soon.",
            link="delivery:success"
        )

        return response

        # ✅ Otherwise allow normal form flow
        


class CourierListView(LoginRequiredMixin, ListView):
    login_url = "users:login"
    template_name = "delivery/list.html"
    context_object_name = "assigned_deliveries"
    
    def dispatch(self, request, *args, **kwargs):
        try:
            courier = Courier.objects.get(user=request.user)
        except Courier.DoesNotExist:
            if CourierApplication.objects.filter(user=request.user):
                return redirect("delivery:success")
            return redirect("delivery:create")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        qs = DeliveryAssignment.objects.filter(courier=user.courier)

        if query:
            qs = qs.filter(
                models.Q(shipment__tracking_number__icontains=query)|
                models.Q(shipment__origin_address__icontains=query) |
                models.Q(shipment__destination_address__icontains=query)
            )

        if status and status != "ALL":
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Shipment.STATUS_CHOICES
        context["selected_status"] = self.request.GET.get("status", "ALL")
        context["query"] = self.request.GET.get("q", "")
        return context
    


class SuccessView(LoginRequiredMixin, TemplateView):
    template_name = "delivery/application_success.html"
    login_url = "users:login"

@login_required(login_url="users:login")
def accept_delivery_view(request, id):
    accepted_shipment = Shipment.objects.get(id=id)
    accepted_shipment.mark_in_transit()

    delivery_assignment_for_this_shipment = DeliveryAssignment.objects.get(shipment=accepted_shipment)
    delivery_assignment_for_this_shipment.mark_accepted()
    return redirect("delivery:list")

@login_required(login_url="users:login")
def delivered_delivery_view(request, id):
    delivered_shipment = Shipment.objects.get(id=id)
    delivered_shipment.mark_delivered()

    delivery_assignment_for_this_shipment = DeliveryAssignment.objects.get(shipment=delivered_shipment)
    delivery_assignment_for_this_shipment.mark_delivered()
    return redirect("delivery:list")
