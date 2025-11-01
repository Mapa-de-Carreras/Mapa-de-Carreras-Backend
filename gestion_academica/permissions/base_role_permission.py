from rest_framework import permissions

class BaseRolePermission(permissions.BasePermission):
    """
    Clase base para permisos basados en roles.
    Subclases deben definir el atributo `role_name`.
    """
    role_name = None  # Debe definirse en las subclases

    def has_permission(self, request, view):
        usuario = request.user

        if not usuario.is_authenticated:
            return False

        # Superusuarios siempre tienen permiso
        if usuario.is_superuser:
            return True

        if not self.role_name:
            raise NotImplementedError(
                f"{self.__class__.__name__} debe definir `role_name`."
            )

        # Comprobación insensible a mayúsculas
        return usuario.roles.filter(nombre__iexact=self.role_name).exists()
