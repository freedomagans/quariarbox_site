from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView, View
from .forms import ShipmentForm
from .models import Shipment
from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.
class ShipmentCreateView(LoginRequiredMixin, CreateView):
    model = Shipment
    template_name = "shipments/create.html"
    form_class = ShipmentForm
    success_url = reverse_lazy("shipments:list")
    login_url = "users:login"

    def form_valid(self, form):
        # assign logged-in user before saving
        form.instance.user = self.request.user
        return super().form_valid(form)


class ShipmentListView(LoginRequiredMixin, ListView):
    model = Shipment
    template_name = "shipments/list.html"
    context_object_name = "shipments"
    login_url = "users:login"

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class ShipmentDetailView(LoginRequiredMixin, DetailView):
    model = Shipment
    template_name = "shipments/detail.html"
    context_object_name = "shipment"
    login_url = "users:login"




class ShipmentUpdateView(LoginRequiredMixin,UpdateView):
    model = Shipment
    template_name = "shipments/update.html"
    form_class = ShipmentForm
    success_url = reverse_lazy("shipments:list")
    login_url = "users:login"


class ShipmentDeleteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        shipment_ids = request.POST.getlist("shipments")
        if shipment_ids:
            Shipment.objects.filter(id__in=shipment_ids, user=request.user).delete()
        return redirect("shipments:list")
