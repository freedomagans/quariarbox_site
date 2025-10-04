from django.urls import path
from .views import *

app_name = "shipments"  # app name for urls

# list of urls for shipments app
urlpatterns = [
    path("", ShipmentCreateView.as_view(), name="create"),  # create shipment url
    path("list/", ShipmentListView.as_view(), name="list"),  # list of shipments page url
    path("<int:pk>", ShipmentDetailView.as_view(), name="detail"),  # detail of shipment page url
    path("<int:pk>/update/", ShipmentUpdateView.as_view(), name="update"),  # update shipment page url
    path("delete/", ShipmentDeleteView.as_view(), name="delete"),  # delete shipment url
    path("track/", track_shipment_view, name="track")  # track shipment page url

]
