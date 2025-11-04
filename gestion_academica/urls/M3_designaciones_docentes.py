# gestion_academica/urls/M2_designaciones_docentes.py

from rest_framework.routers import DefaultRouter
from gestion_academica.views.M3_designaciones_docentes import DesignacionViewSet
from gestion_academica.views.M3_cargos import CargoViewSet

router = DefaultRouter()

# ruta para parametros de regimen
router.register(r"designaciones-docentes", DesignacionViewSet,
                basename="designacion-docente")

# ruta para cargos
router.register(r"cargos", CargoViewSet, basename="cargo")

urlpatterns = router.urls
