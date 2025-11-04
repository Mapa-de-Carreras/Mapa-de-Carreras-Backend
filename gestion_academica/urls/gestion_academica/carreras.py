from django.urls import path
from gestion_academica.views.gestion_academica_views.carreras import (
    CarreraListCreateView,
    CarreraDetailView
)

urlpatterns = [
    path('', CarreraListCreateView.as_view(), name='carrera-list-create'),
    path('<int:pk>/', CarreraDetailView.as_view(), name='carrera-detail'),
]
