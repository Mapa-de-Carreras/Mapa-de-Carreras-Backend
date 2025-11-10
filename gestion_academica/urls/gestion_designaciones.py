from django.urls import path,include
from gestion_academica.views import (
    ComisionListCreateView,
    ComisionDetailView
)
from rest_framework.routers import DefaultRouter
from gestion_academica.views.gestion_designaciones_views.designaciones_docentes import DesignacionViewSet
from gestion_academica.views.gestion_designaciones_views.cargos import CargoViewSet

router = DefaultRouter()
router.register(r"designaciones-docentes", DesignacionViewSet,
                basename="designacion-docente")
router.register(r"cargos", CargoViewSet, basename="cargo")

urlpatterns = [
    path('', include(router.urls)),
    path('comisiones/', ComisionListCreateView.as_view(), name='comision_list_create'),
    path('comisiones/<int:pk>/', ComisionDetailView.as_view(), name='comision_detail'),
]
