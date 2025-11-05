from django.urls import path
from gestion_academica.views.gestion_academica_views.carreras import (
    CarreraListCreateView,
    CarreraDetailView,CarreraVigenciaUpdateView
)

urlpatterns = [
    path('', CarreraListCreateView.as_view(), name='carrera-list-create'),
    path('<int:pk>/', CarreraDetailView.as_view(), name='carrera-detail'),
    path('<int:pk>/vigencia/', CarreraVigenciaUpdateView.as_view(), name='carrera_vigencia'),
]
