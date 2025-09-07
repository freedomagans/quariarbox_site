from django.urls import path
from .views import CourierApplicationView, CourierListView ,SuccessView, accept_delivery_view, delivered_delivery_view
app_name = "delivery"
urlpatterns = [
    path("", CourierApplicationView.as_view(), name="create"),
    path("list/", CourierListView.as_view(), name='list'),
    path("success/", SuccessView.as_view(), name="success"),
    path("<int:id>/accept", accept_delivery_view, name='accept'),
    path("<int:id>/delivered/", delivered_delivery_view, name="delivered")
]
