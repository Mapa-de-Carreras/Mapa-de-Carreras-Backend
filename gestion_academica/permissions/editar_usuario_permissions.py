from rest_framework import permissions
from .admin_permissions import EsAdministrador
from .docente_permissions import EsDocente
from .coordinador_permissions import EsCoordinadorDeCarrera

class UsuarioViewSetPermission(permissions.BasePermission):
    """
    Permiso personalizado para el ViewSet de Usuarios.
    
    Reglas:
    1. Un Admin puede hacer TODO (list, retrieve, update, destroy).
    2. Un usuario NO-Admin (Docente, Coord, etc.) solo puede
       actuar sobre su PROPIO PK.
    3. Si un NO-Admin intenta ver un PK ajeno (exista o no),
       siempre recibirá 403.
    """

    def has_permission(self, request, view):
        # 1. El usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. El Admin siempre tiene permiso para todo.
        if EsAdministrador().has_permission(request, view):
            return True

        # --- Lógica para NO-ADMINISTRADORES ---
        
        # 3. NO-Admins NUNCA pueden listar o destruir.
        if view.action == 'list' or view.action == 'destroy':
            return False # 403 Prohibido

        # 4. Para 'retrieve', 'update', 'partial_update' (acciones con 'pk')
        if view.action in ['retrieve', 'update', 'partial_update']:
            
            # Obtenemos el PK de la URL
            url_pk = view.kwargs.get('pk')
            if not url_pk:
                return False # No debería pasar, pero es seguro.

            # Comparamos el PK de la URL con el PK del usuario logueado
            # (Se castean a string para una comparación segura)
            is_owner = (str(request.user.pk) == str(url_pk))

            if not is_owner:
                # ¡INTENTO DE ACCESO A OTRO USUARIO!
                # (No importa si el PK 'url_pk' existe o no)
                return False # 403 Prohibido
            
            # --- Si ES el dueño (is_owner es True) ---
            
            # Es el dueño, pero ¿qué rol tiene?
            es_docente = EsDocente().has_permission(request, view)
            es_coordinador = EsCoordinadorDeCarrera().has_permission(request, view)
            
            if es_docente or es_coordinador:
                # Es un Docente o Coordinador editando/viendo su perfil.
                return True
            
            # Si es un usuario común (Alumno, etc.)
            # Replicamos la lógica original:
            if request.method in permissions.SAFE_METHODS: # GET
                return True # Puede VER su perfil
            
            return False # NO puede (PATCH) su perfil

        # Cualquier otra acción personalizada se bloquea por defecto
        return False