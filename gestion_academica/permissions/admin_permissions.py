from rest_framework import permissions

class EsAdministrador(permissions.BasePermission):
    """
    Permite el acceso solo a administradores o superusuarios.
    """

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario.is_authenticated:
            return False
        return usuario.is_superuser or usuario.is_staff or usuario.roles.filter(nombre__iexact="ADMINISTRADOR").exists()

