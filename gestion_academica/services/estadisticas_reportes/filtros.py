from django.utils.dateparse import parse_date


def aplicar_filtros_generales(queryset, request):
    """
    Filtros comunes para estadísticas.
    """
    carrera_id = request.query_params.get("carrera_id")
    dedicacion_id = request.query_params.get("dedicacion_id")
    modalidad_id = request.query_params.get("modalidad_id")

    if carrera_id:
        queryset = queryset.filter(
            comision__asignatura__plan_asignatura__plan_de_estudio__carrera_id=carrera_id
        )
    if dedicacion_id:
        queryset = queryset.filter(dedicacion_id=dedicacion_id)
    if modalidad_id:
        queryset = queryset.filter(modalidad_id=modalidad_id)

    return queryset


def aplicar_filtros_designaciones(queryset, request):
    """
    Filtros para DESIGNACIONES:
    - periodo
    - fecha_inicio / fecha_fin
    - dedicacion
    - modalidad
    - carrera
    """

    queryset = aplicar_filtros_generales(queryset, request)

    periodo = request.query_params.get("periodo")
    fecha_inicio = request.query_params.get("fecha_inicio")
    fecha_fin = request.query_params.get("fecha_fin")

    # Periodo cuatrimestral o anual
    if periodo:
        queryset = queryset.filter(
            comision__asignatura__tipo_duracion=periodo
        )

    if fecha_inicio:
        fi = parse_date(fecha_inicio)
        if fi:
            queryset = queryset.filter(fecha_inicio__date__gte=fi)

    if fecha_fin:
        ff = parse_date(fecha_fin)
        if ff:
            queryset = queryset.filter(fecha_inicio__date__lte=ff)

    return queryset
