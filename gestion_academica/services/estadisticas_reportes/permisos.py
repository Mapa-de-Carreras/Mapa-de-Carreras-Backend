# gestion_academica/services/estadisticas_reportes/permisos.py

from rest_framework.exceptions import PermissionDenied
from gestion_academica.models import CarreraCoordinacion, Carrera


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
    
    # --- PERMISOS DE ADMINISTRADOR ---
    # Verificamos si es superusuario O si tiene el rol "Administrador" asignado
    es_admin = user.is_superuser or user.roles.filter(nombre="Administrador").exists()

    if es_admin:
        # Si pidió una carrera específica
        if carrera_id_param is not None:
            try:
                carrera_id = int(carrera_id_param)
                # Opcional: Podrías verificar si la carrera existe en BD, 
                # pero para filtros rápidos basta con devolver el ID.
                return [carrera_id]
            except (TypeError, ValueError):
                raise PermissionDenied("El identificador de carrera es inválido.")
        
        # Si NO pidió carrera específica ("Todas"), el Admin ve TODAS las vigentes
        # Retornamos una lista de IDs de todas las carreras activas
        return list(Carrera.objects.filter(esta_vigente=True).values_list('id', flat=True))

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
