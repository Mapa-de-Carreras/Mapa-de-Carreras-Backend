# gestion_academica/views/estadisticas_reportes_views/estadisticas.py

from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from gestion_academica.models import (
    Designacion,
    Docente,
    ParametrosRegimen,
)
from gestion_academica.services.estadisticas_reportes.permisos import (
    obtener_carreras_para_estadisticas,
)


# ================================================================
# 5.2.0 — DOCENTES POR DEDICACIÓN
# ================================================================
class DocentesPorDedicacionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        carreras_ids = obtener_carreras_para_estadisticas(
            request.user,
            carrera_id_param=request.query_params.get("carrera_id"),
        )

        qs = Designacion.objects.filter(
            fecha_fin__isnull=True,
            comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids,
            docente__dedicacion__isnull=False,
        ).select_related("docente__dedicacion")

        if not qs.exists():
            return Response(
                {
                    "detail": "No hay docentes registrados con designaciones activas en esta carrera."
                },
                status=404,
            )

        total_docentes = qs.values("docente_id").distinct().count()

        agregados = (
            qs.values("docente__dedicacion__nombre")
            .annotate(cantidad=Count("docente", distinct=True))
            .order_by("docente__dedicacion__nombre")
        )

        data = []
        for item in agregados:
            dedicacion = item["docente__dedicacion__nombre"]
            cantidad = item["cantidad"]
            porcentaje = round(cantidad * 100 / total_docentes, 2)

            data.append(
                {
                    "dedicacion": dedicacion,
                    "total_docentes": cantidad,
                    "porcentaje": porcentaje,
                }
            )

        return Response({"total_docentes": total_docentes, "data": data})


# ================================================================
# 5.2.1 — DOCENTES POR MODALIDAD
# ================================================================
class DocentesPorModalidadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        carreras_ids = obtener_carreras_para_estadisticas(
            request.user,
            carrera_id_param=request.query_params.get("carrera_id"),
        )

        qs = Designacion.objects.filter(
            fecha_fin__isnull=True,
            comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids,
            docente__modalidad__isnull=False,
        ).select_related("docente__modalidad")

        if not qs.exists():
            return Response(
                {
                    "detail": "No hay docentes registrados con designaciones activas en esta carrera."
                },
                status=404,
            )

        total_docentes = qs.values("docente_id").distinct().count()

        agregados = (
            qs.values("docente__modalidad__nombre")
            .annotate(cantidad=Count("docente", distinct=True))
            .order_by("docente__modalidad__nombre")
        )

        data = []
        for item in agregados:
            modalidad = item["docente__modalidad__nombre"]
            cantidad = item["cantidad"]
            porcentaje = round(cantidad * 100 / total_docentes, 2)

            data.append(
                {
                    "modalidad": modalidad,
                    "total_docentes": cantidad,
                    "porcentaje": porcentaje,
                }
            )

        return Response({"total_docentes": total_docentes, "data": data})


# ================================================================
# 5.2.2 — HORAS POR DOCENTE
# ================================================================
class HorasPorDocenteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        carreras_ids = obtener_carreras_para_estadisticas(
            request.user,
            carrera_id_param=request.query_params.get("carrera_id"),
        )

        dedicacion_filtro = request.query_params.get("dedicacion")
        modalidad_filtro = request.query_params.get("modalidad")
        horas_min = request.query_params.get("horas_min")
        horas_max = request.query_params.get("horas_max")

        docentes = (
            Docente.objects.filter(
                designaciones__fecha_fin__isnull=True,
                designaciones__comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids,
            )
            .select_related("usuario", "modalidad", "dedicacion")
            .distinct()
        )

        if dedicacion_filtro:
            docentes = docentes.filter(dedicacion__nombre__iexact=dedicacion_filtro)

        if modalidad_filtro:
            docentes = docentes.filter(modalidad__nombre__iexact=modalidad_filtro)

        resultados = []

        for doc in docentes:
            regimen = ParametrosRegimen.objects.filter(
                modalidad=doc.modalidad,
                dedicacion=doc.dedicacion,
                activo=True,
            ).first()

            if not regimen:
                horas_frente = 0
                estado = "SIN_REGIMEN"
            else:
                horas_frente = regimen.horas_max_frente_alumnos
                estado = (
                    "INSUFICIENTE"
                    if horas_frente < regimen.horas_min_frente_alumnos
                    else "DENTRO_DEL_REGIMEN"
                )

            resultados.append(
                {
                    "docente_id": doc.id,
                    "docente": str(doc),
                    "dedicacion": doc.dedicacion.nombre if doc.dedicacion else None,
                    "modalidad": doc.modalidad.nombre if doc.modalidad else None,
                    "total_horas_frente_alumnos": horas_frente,
                    "asignaturas": doc.designaciones.filter(
                        fecha_fin__isnull=True
                    ).count(),
                    "estado_carga": estado,
                }
            )

        if horas_min or horas_max:
            try:
                horas_min = int(horas_min) if horas_min else None
                horas_max = int(horas_max) if horas_max else None
            except ValueError:
                return Response(
                    {"detail": "Los filtros deben ser numéricos."}, status=400
                )

            resultados = [
                r
                for r in resultados
                if (horas_min is None or r["total_horas_frente_alumnos"] >= horas_min)
                and (horas_max is None or r["total_horas_frente_alumnos"] <= horas_max)
            ]

        if not resultados:
            return Response(
                {"detail": "No hay docentes con designaciones activas en esta carrera."},
                status=404,
            )

        resultados.sort(key=lambda x: x["total_horas_frente_alumnos"], reverse=True)

        return Response(resultados)


# ================================================================
# 5.2.3 — DESIGNACIONES POR CARRERA
# ================================================================
class DesignacionesPorCarreraAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        carreras_ids = obtener_carreras_para_estadisticas(
            request.user,
            carrera_id_param=request.query_params.get("carrera_id"),
        )

        asignatura_id = request.query_params.get("asignatura_id")
        tipo_duracion = request.query_params.get("tipo_duracion")
        anio = request.query_params.get("anio")
        estado_comision = request.query_params.get("estado")

        qs = Designacion.objects.filter(
            comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids
        ).select_related(
            "docente__usuario",
            "docente__modalidad",
            "dedicacion",
            "comision__plan_asignatura__asignatura",
        )

        if asignatura_id:
            qs = qs.filter(comision__plan_asignatura__asignatura_id=asignatura_id)

        if tipo_duracion:
            qs = qs.filter(
                comision__plan_asignatura__asignatura__tipo_duracion=tipo_duracion
            )

        if anio:
            try:
                qs = qs.filter(fecha_inicio__year=int(anio))
            except ValueError:
                return Response(
                    {"detail": "El parámetro 'anio' debe ser numérico."}, status=400
                )

        if estado_comision:
            if estado_comision.upper() == "ACTIVA":
                qs = qs.filter(comision__activo=True)
            elif estado_comision.upper() == "INACTIVA":
                qs = qs.filter(comision__activo=False)

        if not qs.exists():
            return Response(
                {
                    "detail": "No se encontraron designaciones registradas para esta carrera."
                },
                status=404,
            )

        data = []
        for d in qs.order_by("-fecha_inicio"):
            plan_asig = d.comision.plan_asignatura
            asignatura = plan_asig.asignatura

            data.append(
                {
                    "asignatura": asignatura.nombre,
                    "docente": str(d.docente),
                    "dedicacion": d.dedicacion.nombre if d.dedicacion else None,
                    "modalidad": d.docente.modalidad.nombre
                    if d.docente.modalidad
                    else None,
                    "periodo": asignatura.tipo_duracion,  # ANUAL / CUATRIMESTRAL
                    "anio": d.fecha_inicio.year,
                    "estado_comision": "ACTIVA" if d.comision.activo else "INACTIVA",
                }
            )

        return Response(data)


# ================================================================
# 5.2.4 — HISTORIAL DOCENTE
# ================================================================
class HistorialDocenteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, docente_id):
        carreras_ids = obtener_carreras_para_estadisticas(
            request.user,
            carrera_id_param=request.query_params.get("carrera_id"),
        )

        ver_todas = request.query_params.get("ver_todas_carreras") == "1"

        docente = get_object_or_404(Docente, pk=docente_id)

        tiene_relacion = Designacion.objects.filter(
            docente=docente,
            comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids,
        ).exists()

        if not tiene_relacion:
            raise PermissionDenied(
                "No tiene permisos para visualizar las designaciones de este docente."
            )

        if ver_todas:
            qs = Designacion.objects.filter(docente=docente).select_related(
                "dedicacion",
                "docente__modalidad",
                "comision__plan_asignatura__asignatura",
                "comision__plan_asignatura__plan_de_estudio__carrera",
            )
        else:
            qs = Designacion.objects.filter(
                docente=docente,
                comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids,
            ).select_related(
                "dedicacion",
                "docente__modalidad",
                "comision__plan_asignatura__asignatura",
                "comision__plan_asignatura__plan_de_estudio__carrera",
            )

        if not qs.exists():
            return Response(
                {"detail": "El docente seleccionado no posee designaciones registradas."},
                status=404,
            )

        data = []
        for d in qs.order_by("fecha_inicio"):
            plan_asig = d.comision.plan_asignatura
            asignatura = plan_asig.asignatura
            carrera = plan_asig.plan_de_estudio.carrera

            data.append(
                {
                    "carrera": carrera.nombre if carrera else None,
                    "asignatura": asignatura.nombre,
                    "periodo": asignatura.tipo_duracion,
                    "anio": d.fecha_inicio.year,
                    "dedicacion": d.dedicacion.nombre if d.dedicacion else None,
                    "modalidad": d.docente.modalidad.nombre
                    if d.docente.modalidad
                    else None,
                    "estado_comision": "ACTIVA" if d.comision.activo else "INACTIVA",
                    "fecha_inicio": d.fecha_inicio,
                    "fecha_fin": d.fecha_fin,
                    "observaciones": d.observacion,
                }
            )

        return Response(
            {
                "docente": str(docente),
                "ver_todas_carreras": ver_todas,
                "designaciones": data,
            }
        )
