from .base_role_permission import BaseRolePermission

class EsAdministrador(BaseRolePermission):
    """Permite acceso a usuarios con rol ADMIN o superusuarios."""
    role_name = "ADMIN"
