from rest_framework import permissions
from django.db.models import Q

class IsCoordinadorOrDocente(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso solo a usuarios
    con rol de Coordinador o Docente.
    """
    message = "No tienes permisos para editar tu perfil. Debes ser Coordinador o Docente."

    def has_permission(self, request, view):
        # El usuario debe estar logueado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificamos si el usuario tiene alguno de los roles requeridos.
        # Esto usa el campo 'roles' que definimos en el modelo Usuario.
        return request.user.roles.filter(
            Q(nombre__iexact="Coordinador") | Q(nombre__iexact="Docente")
        ).exists()