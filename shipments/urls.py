from django.urls import path
from . views import *
app_name = "shipments"
urlpatterns = [
    path("", ShipmentCreateView.as_view(), name="create"),
    path("list/", ShipmentListView.as_view(), name="list"),
    path("<int:pk>", ShipmentDetailView.as_view(), name="detail"),
    path("<int:pk>/update/", ShipmentUpdateView.as_view(), name="update"),
    path("delete/", ShipmentDeleteView.as_view(), name="delete"),

]