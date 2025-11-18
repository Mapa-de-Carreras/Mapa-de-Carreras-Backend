# gestion_academica/services/estadisticas_reportes/permisos.py

from rest_framework.exceptions import PermissionDenied
from gestion_academica.models import CarreraCoordinacion


def obtener_carreras_para_estadisticas(user, carrera_id_param=None):
    """
    Regla de negocio:
    - Solo usuarios coordinadores pueden acceder.
    - Solo pueden ver estadísticas de las carreras que coordinan (CarreraCoordinacion.activo=True).
    - Si se pasa carrera_id, se valida que pertenezca a ese coordinador.
    - Si no se pasa carrera_id, se devuelven TODAS las carreras que coordina.
    """

    if not user.is_authenticated:
        raise PermissionDenied("Debe iniciar sesión para acceder a las estadísticas.")


    if not hasattr(user, "coordinador"):
        raise PermissionDenied("Solo los coordinadores de carrera pueden acceder a este módulo.")

    qs = CarreraCoordinacion.objects.filter(
        coordinador=user.coordinador,
        activo=True
    ).select_related("carrera")

    if not qs.exists():
        raise PermissionDenied("No tiene carreras asignadas como coordinador.")

    carreras_ids = [cc.carrera_id for cc in qs]


    if carrera_id_param is not None:
        try:
            carrera_id = int(carrera_id_param)
        except (TypeError, ValueError):
            raise PermissionDenied("El identificador de carrera es inválido.")

        if carrera_id not in carreras_ids:
            raise PermissionDenied(
                "No tiene permisos para visualizar las estadísticas de esta carrera."
            )
        return [carrera_id]

    # Si no se pasó carrera_id → todas las carreras que coordina
    return carreras_ids
