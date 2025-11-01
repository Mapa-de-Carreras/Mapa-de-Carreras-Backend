from .base_role_permission import BaseRolePermission
from rest_framework import permissions
from gestion_academica.models import Coordinador, CarreraCoordinacion

class EsCoordinador(BaseRolePermission):
    """Permite acceso a usuarios con rol COORDINADOR."""
    role_name = "COORDINADOR"


class EsCoordinadorDeCarrera(permissions.BasePermission):
    """
    Permite modificar solo las carreras que coordina actualmente.
    """
    def has_object_permission(self, request, view, obj):
        usuario = request.user
        if not usuario.is_authenticated:
            return False

        try:
            coordinador = Coordinador.objects.get(id=usuario.id)
        except Coordinador.DoesNotExist:
            return False

        return CarreraCoordinacion.objects.filter(
            carrera=obj,
            coordinador=coordinador,
            activo=True
        ).exists()
