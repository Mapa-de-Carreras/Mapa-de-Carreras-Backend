from rest_framework import permissions
from gestion_academica.models import (
    Coordinador,
    CarreraCoordinacion,
    Carrera,
    PlanDeEstudio,
    Comision,
    Designacion
)

class EsCoordinadorDeCarrera(permissions.BasePermission):
    """
    Permite acceso si el usuario coordinador está activo en alguna carrera
    asociada al objeto (Carrera, PlanDeEstudio, Comision, Designacion).
    """

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        if not usuario.is_authenticated:
            return False

        # Si no es coordinador, no tiene permisos
        if not isinstance(usuario, Coordinador):
            return False

        # Obtener carreras relacionadas según el tipo de objeto
        carreras_relacionadas = self._obtener_carreras_relacionadas(obj)
        if not carreras_relacionadas:
            return False

        # Verificar si el coordinador tiene alguna activa
        return CarreraCoordinacion.objects.filter(
            carrera__in=carreras_relacionadas,
            coordinador=usuario,
            activo=True
        ).exists()

    def _obtener_carreras_relacionadas(self, obj):
        if isinstance(obj, Carrera):
            return [obj]
        elif isinstance(obj, PlanDeEstudio):
            return [obj.carrera] if obj.carrera else []
        elif isinstance(obj, Comision):
            asignatura = getattr(obj, "asignatura", None)
            if not asignatura:
                return []
            return list(Carrera.objects.filter(planes__asignaturas=asignatura).distinct())
        elif isinstance(obj, Designacion):
            comision = getattr(obj, "comision", None)
            asignatura = getattr(comision, "asignatura", None) if comision else None
            return list(Carrera.objects.filter(planes__asignaturas=asignatura).distinct()) if asignatura else []
        return []
