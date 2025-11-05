# gestion_academica/urls/gestion_academica/planes.py
from django.urls import path
from gestion_academica.views.gestion_academica_views import planes

urlpatterns = [
    path('', planes.PlanDeEstudioListCreateView.as_view(), name="plan-list-create"),
    path('<int:pk>/', planes.PlanDeEstudioDetailView.as_view(), name="plan-detail"),
    path("<int:pk>/vigencia/", planes.PlanDeEstudioVigenciaView.as_view(), name="plan-vigencia"),
]
