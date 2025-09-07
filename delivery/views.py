from django.views.generic import CreateView, ListView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import CourierApplication, DeliveryAssignment, Courier
from .forms import CourierApplicationForm
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from shipments.models import Shipment
from django.contrib.auth.decorators import login_required


# Create your views here.
class CourierApplicationView(LoginRequiredMixin,CreateView):
    login_url = "users:login"
    model = CourierApplication
    template_name = "delivery/create.html"
    form_class = CourierApplicationForm
    success_url = reverse_lazy("delivery:success")

    def dispatch(self, request, *args, **kwargs):
        try:
            courier = Courier.objects.get(user=request.user)
            if courier:
                return redirect("delivery:list")
        except Courier.DoesNotExist:
            return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if CourierApplication.objects.filter(user=self.request.user):
            return redirect("delivery:success")


        form.instance.user = self.request.user
        return super().form_valid(form)

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
        return DeliveryAssignment.objects.filter(courier=self.request.user.courier)
    


class SuccessView(LoginRequiredMixin, TemplateView):
    template_name = "delivery/application_success.html"
    login_url = "users:login"

@login_required(login_url="users:login")
def accept_delivery_view(request, id):
    accepted_shipment = Shipment.objects.get(id=id)
    accepted_shipment.status = "IN_TRANSIT"
    accepted_shipment.save()

    delivery_assignment_for_this_shipment = DeliveryAssignment.objects.get(shipment=accepted_shipment)
    delivery_assignment_for_this_shipment.status = "ACCEPTED"
    delivery_assignment_for_this_shipment.save()
    return redirect("delivery:list")

@login_required(login_url="users:login")
def delivered_delivery_view(request, id):
    delivered_shipment = Shipment.objects.get(id=id)
    delivered_shipment.status = "DELIVERED"
    delivered_shipment.save()

    delivery_assignment_for_this_shipment = DeliveryAssignment.objects.get(shipment=delivered_shipment)
    delivery_assignment_for_this_shipment.status = "DELIVERED"
    delivery_assignment_for_this_shipment.save()
    return redirect("delivery:list")
