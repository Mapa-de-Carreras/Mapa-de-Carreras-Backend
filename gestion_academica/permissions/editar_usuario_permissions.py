from rest_framework import permissions
from .admin_permissions import EsAdministrador
from .docente_permissions import EsDocente
from .coordinador_permissions import EsCoordinadorDeCarrera

class UsuarioViewSetPermission(permissions.BasePermission):
    """
    Permiso personalizado para el ViewSet de Usuarios que
    reutiliza los permisos modulares.
    """

    def has_permission(self, request, view):
        # 1. El usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Reutilizamos EsAdministrador para la lista y borrado
        if view.action == 'list' or view.action == 'destroy':
            return EsAdministrador().has_permission(request, view)

        # 3. Para otras acciones (retrieve, update, partial_update),
        #    dejamos que 'has_object_permission' decida.
        return True

    def has_object_permission(self, request, view, obj):
        # 'obj' es el usuario que se está intentando ver/editar
        # 'request.user' es el usuario que hace la petición
        
        # 1. Admin (reutilizando EsAdministrador )
        if EsAdministrador().has_permission(request, view):
            return True

        # 2. Es el dueño de la cuenta?
        is_owner = (request.user == obj)

        # 3. Lógica para Coordinador (reutilizando EsCoordinadorDeCarrera)
        if EsCoordinadorDeCarrera().has_permission(request, view):
            # Comprueba si el objetivo ('obj') es un docente
            target_es_docente = obj.roles.filter(nombre__iexact="DOCENTE").exists()
            # Un Coordinador puede editarse a sí mismo O a un Docente
            return is_owner or target_es_docente

        # 4. Lógica para Docente (reutilizando EsDocente)
        if EsDocente().has_permission(request, view):
            # Un Docente solo puede editarse a sí mismo
            return is_owner
        
        # 5. Usuario Común (sin esos roles)
        # Solo puede VER (GET) su propio perfil, no editarlo (PATCH)
        if request.method in permissions.SAFE_METHODS: # SAFE_METHODS son GET, HEAD, OPTIONS
            return is_owner
        
        # Si es un usuario común intentando un PATCH, falla
        return False