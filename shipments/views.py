"""
Defining views(processes requests and returns appropriate responses) for the shipments app
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView, View
from .forms import ShipmentForm
from .models import Shipment
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseNotFound
from delivery.models import DeliveryAssignment

class ShipmentCreateView(LoginRequiredMixin, CreateView):
    """
    defining view to process request for shipment creation page
    """
    model = Shipment  # binds view to model
    template_name = "shipments/create.html"  # template to render
    form_class = ShipmentForm  # binds form to this view
    success_url = reverse_lazy("shipments:list")  # redirects to shipment list page on successful creation of shipment
    login_url = "users:login"  # login page if not authenticated

    def form_valid(self, form):
        # assign logged-in user before saving
        form.instance.user = self.request.user
        messages.success(self.request, "Shipment created.")  # sends success message to displayed page
        return super().form_valid(form)


class ShipmentListView(LoginRequiredMixin, ListView):
    """
    processes request for the shipments list page 
    """
    model = Shipment  # binds model to this view
    template_name = "shipments/list.html"  # template to render
    context_object_name = "shipments"  # the context name referenced in the template
    login_url = "users:login"  # login page if not authenticated


    def get_queryset(self):
        """overrides method to process the object to be returned and referenced as the context_object in the template """
        user = self.request.user  # authenticated user
        query = self.request.GET.get("q")  # search parameter 'q' passed from the page to search through shipments
        status = self.request.GET.get("status")  # status parameter passed from the page to filter shipments

        qs = Shipment.objects.filter(user=user).order_by("-created_at")  # shipments for authenticated user

        if query:
            # filters shipments based on search  parameter 'query'
            qs = qs.filter(
                models.Q(tracking_number__icontains=query) |
                models.Q(origin_address__icontains=query) |
                models.Q(destination_address__icontains=query)
            )

        if status and status != "ALL":
            # filters shipments based on status parameter from the page
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        """
        process the context_data for the page 
        """
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Shipment.STATUS_CHOICES  # context reference for status_choices on the model
        context["selected_status"] = self.request.GET.get("status", "ALL")  # context reference for selected_status
        context["query"] = self.request.GET.get("q", "")  # context reference for the passed search parameter 'query'
        return context


class ShipmentDetailView(LoginRequiredMixin, DetailView):
    """process request for a shipment detail page"""
    model = Shipment  # binds view to the Shipment model
    template_name = "shipments/detail.html"  # template to render
    context_object_name = "shipment"  # context reference for the Shipment instance
    login_url = "users:login"  # login page if not authenticated
 

    def get_queryset(self):
        """
        only user who own shipment see's details
        except they are couriers which can view detals just to accept
        shipment and mark as delivered
        """
        owned_shipments = Shipment.objects.filter(user=self.request.user)
        assigned_shipments = Shipment.objects.filter(deliveryassignment__courier__user=self.request.user)

        
        return owned_shipments or assigned_shipments

        
    


class ShipmentUpdateView(LoginRequiredMixin, UpdateView):
    """
    processes requests for the update shipment page
    """
    model = Shipment  # binds view to Shipment model
    template_name = "shipments/update.html"  # template to render
    form_class = ShipmentForm  # binds form to this view
    success_url = reverse_lazy("shipments:list")  # page to render on succesful update
    login_url = "users:login"  # login page if not authenticated

    def form_valid(self, form):
        """validates form"""
        messages.success(self.request,
                         f"Shipment {form.instance.tracking_number} updated.")  # sends success message on displayed page
        form.instance.calc_cost()
        return super().form_valid(form)
    
    def get_queryset(self):
        return Shipment.objects.filter(user=self.request.user) # filtering resultset so only owners update their shipments


class ShipmentDeleteView(LoginRequiredMixin, View):
    """processes the request for deleting shipments """
    login_url = 'users:login' # login page 

    def post(self, request, *args, **kwargs):
        """processes request for bulk delete"""
        shipment_ids = request.POST.getlist(
            "shipments")  # retrieves list of selected shipments on the shipment list page
        if shipment_ids:
            user_shipments = Shipment.objects.filter(id__in=shipment_ids,
                                    user=request.user)  # filters shipments for user
            if user_shipments :
                user_shipments.delete() # deletes shipments
                
                messages.warning(request, "shipments deleted.")  # sends message on displayed page
                return redirect("shipments:list")  # redirects to shipment list page
            else:
                return HttpResponseNotFound()# returns not allowed http status


def track_shipment_view(request):
    """ processes request to track shipment on the track shipment page """
    shipment = None
    error = None

    if request.method == "POST":
        tracking_number = request.POST.get(
            "tracking_number").strip()  # retrieves tracking_number passed to the view by the track shipment page
        try:
            shipment = Shipment.objects.get(
                tracking_number=tracking_number)  # gets the shipment based on tracking_number
        except Shipment.DoesNotExist:
            error = "No shipment found with that tracking number."  # error if shipment is not found
    return render(request, "shipments/track.html", {"shipment": shipment,
                                                    "error": error})  # renders template and passes the context dictionary accordingly
