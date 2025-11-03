
from rest_framework import permissions

class EsDocente(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con rol Docente.
    """
    def has_permission(self, request, view):
        usuario = request.user
        return usuario.is_authenticated and usuario.roles.filter(nombre__iexact="DOCENTE").exists()
