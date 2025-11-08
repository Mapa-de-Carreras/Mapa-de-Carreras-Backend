from django.urls import path
from gestion_academica.views import (
    ComisionListCreateView,
    ComisionDetailView
)

urlpatterns = [
    path('comisiones/', ComisionListCreateView.as_view(), name='comision_list_create'),
    path('comisiones/<int:pk>/', ComisionDetailView.as_view(), name='comision_detail'),
]
