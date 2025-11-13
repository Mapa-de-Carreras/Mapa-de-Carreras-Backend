# gestion_academica/views/M2_gestion_catalogos.py

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from gestion_academica import models
from gestion_academica.serializers.M3_designaciones_docentes import CargoSerializer


class BaseAdminCoordinadorViewSet(viewsets.ModelViewSet):
    '''
    Restringe creacion/actualizacion/borrado a admin o coordinador
    '''
    permission_classes = [IsAuthenticated]

    def _user_can_manage(self, user):
        return user.is_superuser or user.roles.filter(nombre__in=["Admin", "Coordinador"]).exists()

    def create(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para crear cargos.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para modificar cargos.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para modificar cargos.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para eliminar cargos.")
        return super().destroy(request, *args, **kwargs)


# VIEWSETS para cargo
class CargoViewSet(BaseAdminCoordinadorViewSet):
    '''
    Listar/crear/actualizar cargo
    '''
    queryset = models.Cargo.objects.all().order_by("id")
    serializer_class = CargoSerializer
