from django.db.models import Count, Sum
from django.contrib.auth import get_user_model

from gestion_academica.models.M1_gestion_academica import Carrera
from gestion_academica.models.M2_gestion_docentes import Docente, ParametrosRegimen
from gestion_academica.models.M3_designaciones_docentes import Designacion
from gestion_academica.models.M4_gestion_usuarios_autenticacion import Coordinador, Rol

Usuario = get_user_model()


# --------------------------
# Helpers de rol / carrera
# --------------------------

def es_admin(usuario: Usuario) -> bool:
    if getattr(usuario, "is_superuser", False):
        return True
    # si usás rol "Administrador"
    return usuario.roles.filter(nombre__iexact="Administrador").exists()


def get_carrera_del_coordinador(usuario: Usuario) -> Carrera | None:
    """
    Devuelve la primera carrera activa del coordinador logueado.
    Si no es coordinador o no tiene carrera activa, devuelve None.
    """
    coord = getattr(usuario, "coordinador", None)
    if coord is None:
        return None

    return coord.carreras_coordinadas.filter(
        carreracoordinacion__activo=True,
        carreracoordinacion__fecha_fin__isnull=True
    ).first()


def get_carrera_para_estadisticas(usuario: Usuario, carrera_id_param: str | None):
    """
    Lógica común:
    - Si es admin:
        - si viene carrera_id -> esa carrera
        - si no viene -> None (estadísticas globales)
    - Si es coordinador:
        - ignora carrera_id externo y usa su carrera activa
    - Si no es ninguno -> None
    """
    if es_admin(usuario):
        if carrera_id_param:
            try:
                return Carrera.objects.get(pk=carrera_id_param)
            except Carrera.DoesNotExist:
                return "CARRERA_INVALIDA"
        return None  # global para admin

    # Coordinador
    carrera = get_carrera_del_coordinador(usuario)
    if carrera is None:
        return "SIN_CARRERA_COORD"
    return carrera


# --------------------------
# 5.2.0 - Docentes por dedicación
# --------------------------

def docentes_por_dedicacion_qs(usuario: Usuario, carrera_id_param: str | None):
    carrera = get_carrera_para_estadisticas(usuario, carrera_id_param)

    if carrera == "CARRERA_INVALIDA":
        return "CARRERA_INVALIDA"
    if carrera == "SIN_CARRERA_COORD":
        return "SIN_CARRERA_COORD"

    qs = Docente.objects.filter(activo=True)

    if carrera is not None:
        qs = qs.filter(
            designaciones__comision__asignatura__planes_de_estudio__carrera=carrera,
            designaciones__fecha_fin__isnull=True
        )

    return qs.values("dedicacion__nombre").annotate(total=Count("id", distinct=True))


# --------------------------
# 5.2.1 - Docentes por modalidad
# --------------------------

def docentes_por_modalidad_qs(usuario: Usuario, carrera_id_param: str | None):
    carrera = get_carrera_para_estadisticas(usuario, carrera_id_param)

    if carrera == "CARRERA_INVALIDA":
        return "CARRERA_INVALIDA"
    if carrera == "SIN_CARRERA_COORD":
        return "SIN_CARRERA_COORD"

    qs = Docente.objects.filter(activo=True)

    if carrera is not None:
        qs = qs.filter(
            designaciones__comision__asignatura__planes_de_estudio__carrera=carrera,
            designaciones__fecha_fin__isnull=True
        )

    return qs.values("modalidad__nombre").annotate(total=Count("id", distinct=True))


# --------------------------
# 5.2.2 - Horas por docente
# --------------------------

def horas_por_docente_qs(
    usuario: Usuario,
    carrera_id_param: str | None,
    dedicacion_nombre: str | None,
    modalidad_nombre: str | None
):
    carrera = get_carrera_para_estadisticas(usuario, carrera_id_param)

    if carrera == "CARRERA_INVALIDA":
        return "CARRERA_INVALIDA"
    if carrera == "SIN_CARRERA_COORD":
        return "SIN_CARRERA_COORD"

    qs = Designacion.objects.filter(
        fecha_fin__isnull=True,
    )

    if carrera is not None:
        qs = qs.filter(
            comision__asignatura__planes_de_estudio__carrera=carrera
        )

    if dedicacion_nombre:
        qs = qs.filter(docente__dedicacion__nombre__iexact=dedicacion_nombre)

    if modalidad_nombre:
        qs = qs.filter(docente__modalidad__nombre__iexact=modalidad_nombre)

    # agregamos por docente
    agregados = qs.values(
        "docente__id",
        "docente__usuario__first_name",
        "docente__usuario__last_name",
        "docente__dedicacion__nombre",
        "docente__modalidad__nombre",
    ).annotate(
        total_horas=Sum("horas_frente_alumnos"),
        asignaturas=Count("comision__asignatura", distinct=True)
    ).order_by("-total_horas")

    # calculamos estado de carga según ParametrosRegimen
    resultados = []
    for row in agregados:
        dedicacion = row["docente__dedicacion__nombre"]
        modalidad = row["docente__modalidad__nombre"]
        regimen = ParametrosRegimen.objects.filter(
            dedicacion__nombre=dedicacion,
            modalidad__nombre=modalidad,
            activo=True
        ).first()

        estado = "SIN_REGIMEN"
        if regimen:
            if row["total_horas"] > regimen.horas_max_frente_alumnos:
                estado = "EXCESO"
            elif row["total_horas"] < regimen.horas_min_frente_alumnos:
                estado = "INSUFICIENTE"
            else:
                estado = "OK"

        row_with_estado = {
            **row,
            "estado_carga": estado
        }
        resultados.append(row_with_estado)

    return resultados


# --------------------------
# 5.2.3 - Designaciones de la carrera
# --------------------------

def designaciones_carrera_qs(usuario: Usuario, carrera_id_param: str | None):
    carrera = get_carrera_para_estadisticas(usuario, carrera_id_param)

    if carrera == "CARRERA_INVALIDA":
        return "CARRERA_INVALIDA"
    if carrera == "SIN_CARRERA_COORD":
        return "SIN_CARRERA_COORD"

    qs = Designacion.objects.select_related(
        "docente__usuario",
        "comision__asignatura",
        "dedicacion",
        "modalidad",
    )

    if carrera is not None:
        qs = qs.filter(
            comision__asignatura__planes_de_estudio__carrera=carrera
        )

    return qs.order_by("-fecha_inicio")


# --------------------------
# 5.2.4 - Historial de un docente
# --------------------------

def historial_docente_qs(
    usuario: Usuario,
    docente_id: int,
    carrera_id_param: str | None,
    incluir_todas_carreras: bool
):
    """
        - Para coordinador: por defecto solo su carrera.
        Si incluir_todas_carreras=True, se limita a lo que razonablemente pueda ver el coordinador).
        - Para admin: puede ver todas las carreras.
    """
    carrera = get_carrera_para_estadisticas(usuario, carrera_id_param)

    if carrera == "CARRERA_INVALIDA":
        return "CARRERA_INVALIDA"
    if carrera == "SIN_CARRERA_COORD":
        return "SIN_CARRERA_COORD"

    qs = Designacion.objects.filter(
        docente_id=docente_id
    ).select_related(
        "comision__asignatura",
        "dedicacion",
        "modalidad",
    ).order_by("fecha_inicio")

    if not es_admin(usuario):
        # coordinador: si no pide todas, filtramos por su carrera; 
        if carrera is not None and not incluir_todas_carreras:
            qs = qs.filter(
                comision__asignatura__planes_de_estudio__carrera=carrera
            )
    else:
        # admin: si se pasa carrera_id, filtramos; si no, ve todo
        if carrera is not None:
            qs = qs.filter(
                comision__asignatura__planes_de_estudio__carrera=carrera
            )

    return qs
