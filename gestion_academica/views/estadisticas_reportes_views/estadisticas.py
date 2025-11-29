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
from django.db.models import Sum
class HorasPorDocenteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(f"DEBUG BACKEND - carrera_id recibido: {request.query_params.get('carrera_id')}")
        carreras_ids = obtener_carreras_para_estadisticas(
            request.user,
            carrera_id_param=request.query_params.get("carrera_id"),
        )

        filtros_extra = {}
        if request.query_params.get("dedicacion"):
            filtros_extra["dedicacion__nombre__iexact"] = request.query_params.get("dedicacion")
        if request.query_params.get("modalidad"):
            filtros_extra["modalidad__nombre__iexact"] = request.query_params.get("modalidad")

        # 2. BUSCAR DOCENTES:
        # Traemos solo los docentes que tengan designaciones activas en el alcance seleccionado
        docentes = (
            Docente.objects.filter(
                designaciones__activo=True, # Designacion activa
                designaciones__comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids,
                **filtros_extra
            )
            .select_related("usuario", "modalidad", "dedicacion")
            .distinct()
        )

        resultados = []

        # 3. CALCULAR HORAS (Aquí estaba el problema antes):
        for doc in docentes:
            # FILTRO CLAVE:
            # En lugar de sumar 'todas' las designaciones del docente, sumamos SOLO
            # las que pertenecen a 'carreras_ids'.
            # - Si seleccionaste 'Todas', sumará todo el paquete.
            # - Si seleccionaste 'Sistemas', sumará solo horas de Sistemas.
            designaciones_validas = doc.designaciones.filter(
                activo=True,
                comision__plan_asignatura__plan_de_estudio__carrera_id__in=carreras_ids
            )

            # Si tras filtrar no queda nada (caso borde), saltamos
            if not designaciones_validas.exists():
                continue

            # CALCULO DE HORAS (CORREGIDO SEGÚN TUS MODELOS M1 y M3)
            # Ruta correcta: Designacion -> Comision -> PlanAsignatura -> horas_semanales
            agregado = designaciones_validas.aggregate(
                total_horas=Sum('comision__plan_asignatura__horas_semanales')
            )
            total_horas = agregado['total_horas'] or 0
            
            # Contar asignaturas únicas (usando el plan_asignatura para evitar duplicados si hay varias comisiones de la misma materia)
            cantidad_asignaturas = designaciones_validas.values('comision__plan_asignatura').distinct().count()

            # LÓGICA DE RÉGIMEN
            # Buscamos el régimen que corresponde a la situación contractual del docente
            regimen = ParametrosRegimen.objects.filter(
                modalidad=doc.modalidad,
                dedicacion=doc.dedicacion,
                activo=True,
            ).first()

            estado = "SIN_REGIMEN"
            if regimen:
                if total_horas < regimen.horas_min_frente_alumnos:
                    estado = "INSUFICIENTE"
                elif total_horas > regimen.horas_max_frente_alumnos: # Opcional: Warning si se pasa
                    estado = "EXCEDIDO"
                else:
                    estado = "DENTRO_DEL_REGIMEN"

            # 4. APLICAR FILTROS DE RANGO DE HORAS (Post-cálculo)
            horas_min_param = request.query_params.get("horas_min")
            horas_max_param = request.query_params.get("horas_max")
            
            try:
                if horas_min_param and total_horas < int(horas_min_param):
                    continue
                if horas_max_param and total_horas > int(horas_max_param):
                    continue
            except ValueError:
                pass # Ignorar filtros numéricos mal formados

            resultados.append(
                {
                    "docente_id": doc.id,
                    "docente": f"{doc.usuario.last_name} {doc.usuario.first_name}", # Usamos los campos de usuario directo
                    "dedicacion": doc.dedicacion.nombre if doc.dedicacion else "-",
                    "modalidad": doc.modalidad.nombre if doc.modalidad else "-",
                    "total_horas_frente_alumnos": total_horas,
                    "asignaturas": cantidad_asignaturas,
                    "estado_carga": estado,
                }
            )

        # Ordenar por horas descendente para ver a los más cargados primero
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
