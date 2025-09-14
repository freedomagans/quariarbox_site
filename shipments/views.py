from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView, View
from .forms import ShipmentForm
from .models import Shipment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.contrib import messages

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
        messages.success(self.request,"Shipment created.")
        return super().form_valid(form)


class ShipmentListView(LoginRequiredMixin, ListView):
    model = Shipment
    template_name = "shipments/list.html"
    context_object_name = "shipments"
    login_url = "users:login"

    def get_queryset(self):
        user = self.request.user
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        qs = Shipment.objects.filter(user=user).order_by("-created_at")

        if query:
            qs = qs.filter(
                models.Q(tracking_number__icontains=query)|
                models.Q(origin_address__icontains=query) |
                models.Q(destination_address__icontains=query)
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

    def form_valid(self, form):
        messages.success(self.request,f"Shipment {form.instance.tracking_number} updated.")
        return super().form_valid(form)
    


class ShipmentDeleteView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        shipment_ids = request.POST.getlist("shipments")
        if shipment_ids:
            Shipment.objects.filter(id__in=shipment_ids, user=request.user).delete()
            messages.warning(request,"shipments deleted.")
        return redirect("shipments:list")
