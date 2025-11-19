from rest_framework import permissions
from gestion_academica.models import (
    Coordinador,
    CarreraCoordinacion,
    Carrera,
    PlanDeEstudio,
    Comision,
    Designacion,
    PlanAsignatura # <-- Importante
)

class EsCoordinadorDeCarrera(permissions.BasePermission):
    """
    Permiso "inteligente" para Coordinadores (Versión Corregida).
    
    1. has_permission: Comprueba si el usuario es un Coordinador activo.
    2. has_object_permission: Comprueba si el 'obj' que se está
       viendo/editando (ej: Designacion, Comision) pertenece
       a una de las carreras activas del coordinador.
    """

    def has_permission(self, request, view):
        """
        Comprueba si el usuario está autenticado Y
        si es un Admin O un Coordinador activo.
        """
        usuario = request.user
        if not usuario.is_authenticated:
            return False

        # --- ARREGLO ---
        # 1. Permitir siempre al Admin
        if usuario.is_superuser or usuario.is_staff or usuario.roles.filter(nombre__iexact="ADMINISTRADOR").exists():
            return True
        
        # 2. Si no es Admin, comprobar si es un Coordinador activo
        return (
            hasattr(usuario, 'coordinador') and
            usuario.coordinador.activo
        )

    def has_object_permission(self, request, view, obj):
        """
        Comprueba si el usuario tiene permiso sobre el objeto 'obj'.
        """
        # Admin siempre tiene permiso
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Obtenemos el perfil de coordinador del usuario
        try:
            coordinador_perfil = request.user.coordinador
        except Coordinador.DoesNotExist:
            return False # No tiene perfil

        # --- ARREGLO 2: Lógica de 'obtener carreras' corregida ---
        carreras_relacionadas = []
        
        if isinstance(obj, Carrera):
            carreras_relacionadas = [obj]
            
        elif isinstance(obj, PlanDeEstudio):
            carreras_relacionadas = [obj.carrera] if obj.carrera else []
        
        elif isinstance(obj, PlanAsignatura):
             carreras_relacionadas = [obj.plan_de_estudio.carrera] if obj.plan_de_estudio.carrera else []

        elif isinstance(obj, Comision):
            # Ruta: Comision -> PlanAsignatura -> PlanDeEstudio -> Carrera
            try:
                carreras_relacionadas = [obj.plan_asignatura.plan_de_estudio.carrera]
            except AttributeError:
                carreras_relacionadas = []
            
        elif isinstance(obj, Designacion):
            # Ruta: Designacion -> Comision -> PlanAsignatura -> PlanDeEstudio -> Carrera
            try:
                carreras_relacionadas = [obj.comision.plan_asignatura.plan_de_estudio.carrera]
            except AttributeError:
                carreras_relacionadas = []
        
        # Si 'obj' es un Perfil Coordinador (para el CoordinadorViewSet)
        elif isinstance(obj, Coordinador):
            # El coordinador solo puede ver/editar su propio perfil
            return obj.usuario == request.user

        if not carreras_relacionadas:
            return False # No pudimos determinar una carrera para el objeto

        # --- Comprobación Final (Corregida) ---
        # ¿Es el usuario un coordinador ACTIVO de ALGUNA
        # de las carreras relacionadas con este objeto?
        return CarreraCoordinacion.objects.filter(
            carrera__in=carreras_relacionadas,
            coordinador=coordinador_perfil, # <-- Usamos el perfil
            activo=True
        ).exists()