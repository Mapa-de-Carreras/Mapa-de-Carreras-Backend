# gestion_academica/urls/M2_gestion_docentes.py

from rest_framework.routers import DefaultRouter
from gestion_academica.views.M2_gestion_docentes import DocenteViewSet
from gestion_academica.views.M2_gestion_catalogos import ModalidadViewSet, CaracterViewSet, DedicacionViewSet
from gestion_academica.views.M2_parametros_regimen import ParametrosRegimenViewSet

router = DefaultRouter()
# ruta para docentes
router.register(r"docentes", DocenteViewSet, basename="docente")

# ruta para los catalogos (modalidad, caracter, dedicacion)
router.register(r"modalidades", ModalidadViewSet, basename="modalidad")
router.register(r"caracteres", CaracterViewSet, basename="caracter")
router.register(r"dedicaciones", DedicacionViewSet, basename="dedicacion")

# ruta para parametros de regimen
router.register(r"parametros-regimen", ParametrosRegimenViewSet,
                basename="parametros-regimen")

urlpatterns = router.urls
