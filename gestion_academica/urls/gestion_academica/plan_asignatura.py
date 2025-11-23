from django.urls import path
from gestion_academica.views.gestion_academica_views import   PlanAsignaturaListCreateView, PlanAsignaturaDetailView

urlpatterns = [
   path("", PlanAsignaturaListCreateView.as_view(),name="plan_asignatura_list_create"),
   path("<int:pk>/", PlanAsignaturaDetailView.as_view(), name="plan_asignatura_detail"),
]   