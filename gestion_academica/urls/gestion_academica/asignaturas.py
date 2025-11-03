from django.urls import path
from gestion_academica.views.gestion_academica_views.asignaturas import (
    AsignaturaListCreateView,
    AsignaturaDetailView
)

urlpatterns = [
    path("", AsignaturaListCreateView.as_view(), name="asignatura-list-create"),
    path("<int:pk>/", AsignaturaDetailView.as_view(), name="asignatura-detail"),
]
