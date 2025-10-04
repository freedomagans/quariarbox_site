from django.urls import path
from .views import CourierApplicationView, CourierListView, SuccessView, accept_delivery_view, delivered_delivery_view

app_name = "delivery"  # app name

# list of urls
urlpatterns = [
    path("", CourierApplicationView.as_view(), name="create"),  # url for courier application page
    path("list/", CourierListView.as_view(), name='list'),  # url for list of assinged deliveries for courier
    path("success/", SuccessView.as_view(), name="success"),  # url for success page on successful application
    path("<int:id>/accept", accept_delivery_view, name='accept'),  # url for accepting assigned delivery
    path("<int:id>/delivered/", delivered_delivery_view, name="delivered")  # url fo r delivering assigned delivery
]
