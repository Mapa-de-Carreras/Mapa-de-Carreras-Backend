from rest_framework import permissions
from gestion_academica.models import Coordinador, CarreraCoordinacion


class EsCoordinadorDeCarrera(permissions.BasePermission):
    """
    Permite editar solo carreras que el usuario coordina actualmente.
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

