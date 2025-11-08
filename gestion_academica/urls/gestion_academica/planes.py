# gestion_academica/urls/gestion_academica/planes.py
from django.urls import path
from gestion_academica.views.gestion_academica_views import planes

urlpatterns = [
    path('', planes.PlanDeEstudioListCreateView.as_view(), name="plan-list-create"),
    path('<int:pk>/', planes.PlanDeEstudioDetailView.as_view(), name="plan-detail"),
    path("<int:pk>/vigencia/", planes.PlanDeEstudioVigenciaView.as_view(), name="plan-vigencia"),
    path("correlativas/", planes.ListarCorrelativasDeAsignaturaView.as_view(), name="listar-correlativas"),
    path('asociar-asignatura/', planes.AsociarAsignaturaAPlanView.as_view(), name='asociar-asignatura-plan'),
    path('desasociar-asignatura/<int:plan_id>/<int:asignatura_id>/', 
         planes.DesasociarAsignaturaDePlanView.as_view(), 
         name='desasociar-asignatura-plan'),
    path("asignar-correlativa/", planes.AsignarCorrelativaView.as_view(), name="asignar-correlativa"),
    path("correlativas/<int:pk>/", planes.EliminarCorrelativaView.as_view(), name="eliminar-correlativa"),
]
