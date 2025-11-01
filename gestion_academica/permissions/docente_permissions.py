from .base_role_permission import BaseRolePermission

class EsDocente(BaseRolePermission):
    """Permite acceso a usuarios con rol DOCENTE."""
    role_name = "DOCENTE"
