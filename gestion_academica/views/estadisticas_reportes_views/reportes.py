# gestion_academica/views/estadisticas_reportes_views/reportes_exportacion.py

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.http import HttpResponse

from gestion_academica.services.estadisticas_reportes.permisos import (
    obtener_carreras_para_estadisticas,
)

from .estadisticas import (
    DocentesPorDedicacionAPIView,
    DocentesPorModalidadAPIView,
    HorasPorDocenteAPIView,
    DesignacionesPorCarreraAPIView,
)

import csv
from io import StringIO, BytesIO
from openpyxl import Workbook

# ---------------- PDF ----------------
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet


class ExportarEstadisticasAPIView(APIView):
    """
    RF [5.3] - Exportar Datos
    Tipo:
        - DEDICACION
        - MODALIDAD
        - HORAS
        - DESIGNACIONES
    Formato:
        - csv
        - xlsx
        - pdf
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipo = request.query_params.get("tipo")
        formato = request.query_params.get("formato")
        carrera_id = request.query_params.get("carrera_id")

        if tipo not in ["DEDICACION", "MODALIDAD", "HORAS", "DESIGNACIONES"]:
            raise ValidationError("Tipo inválido.")

        if formato not in ["csv", "xlsx", "pdf"]:
            raise ValidationError("Formato inválido. Use csv, xlsx o pdf.")

        obtener_carreras_para_estadisticas(request.user, carrera_id_param=carrera_id)

        # ============================================================
        # OBTENER LOS DATOS SEGÚN TIPO
        # ============================================================
        if tipo == "DEDICACION":
            data = DocentesPorDedicacionAPIView().get(request).data.get("data", [])
            fieldnames = ["dedicacion", "total_docentes", "porcentaje"]
            nombre_archivo = "docentes_por_dedicacion"

        elif tipo == "MODALIDAD":
            data = DocentesPorModalidadAPIView().get(request).data.get("data", [])
            fieldnames = ["modalidad", "total_docentes", "porcentaje"]
            nombre_archivo = "docentes_por_modalidad"

        elif tipo == "HORAS":
            data = HorasPorDocenteAPIView().get(request).data
            fieldnames = [
                "docente",
                "dedicacion",
                "modalidad",
                "total_horas_frente_alumnos",
                "asignaturas",
                "estado_carga",
            ]
            nombre_archivo = "horas_por_docente"

        else:  # DESIGNACIONES
            raw = DesignacionesPorCarreraAPIView().get(request).data

            #PERIODO = tipo_duracion (ANUAL / CUATRIMESTRAL)
            data = []
            for d in raw:
                data.append(
                    {
                        "asignatura": d["asignatura"],
                        "docente": d["docente"],
                        "dedicacion": d["dedicacion"],
                        "modalidad": d["modalidad"],
                        "periodo": d["periodo"],  # ya corregido
                        "anio": d["anio"],
                        "estado_comision": d["estado_comision"],
                    }
                )

            fieldnames = [
                "Asignatura",
                "Docente",
                "Dedicacion",
                "Modalidad",
                "Periodo",
                "Anio",
                "Estado de comision",
            ]
            nombre_archivo = "designaciones_carrera"

        # ============================================================
        # EXPORTAR CSV
        # ============================================================
        if formato == "csv":
            buffer = StringIO()
            writer = csv.DictWriter(buffer, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow({k: row.get(k, "") for k in fieldnames})

            resp = HttpResponse(buffer.getvalue(), content_type="text/csv")
            resp["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.csv"'
            return resp

        # ============================================================
        # EXPORTAR XLSX
        # ============================================================
        if formato == "xlsx":
            wb = Workbook()
            ws = wb.active
            ws.append(fieldnames)
            for row in data:
                ws.append([row.get(k, "") for k in fieldnames])

            output = BytesIO()
            wb.save(output)
            output.seek(0)

            resp = HttpResponse(
                output.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            resp["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.xlsx"'
            return resp

        # ============================================================
# EXPORTAR PDF CON LOGO UNTDFF + LANDSCAPE + ANCHO AJUSTADO
# ============================================================
        if formato == "pdf":
            buffer = BytesIO()

            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors

            # Documento horizontal (landscape)
            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(A4),
                leftMargin=40,
                rightMargin=40,
                topMargin=50,
                bottomMargin=30,
            )

            styles = getSampleStyleSheet()
            story = []

            # -----------------------------
            # LOGO INSTITUCIONAL UNTDFF
            # -----------------------------
            try:
                logo_path = "gestion_academica/static/gestion_academica/logo_untdf.png"
                logo = Image(logo_path, width=120, height=60)   # ajusta tamaño si querés
                story.append(logo)
            except Exception:
                pass  # si falla no rompe el PDF

            story.append(Spacer(1, 12))

            # -----------------------------
            # Título
            # -----------------------------
            titulo = f"<b>Reporte: {nombre_archivo.replace('_', ' ').title()}</b>"
            story.append(Paragraph(titulo, styles["Title"]))
            story.append(Spacer(1, 20))

            # -----------------------------
            # TABLA
            # -----------------------------
            table_data = [fieldnames]
            for row in data:
                table_data.append([Paragraph(str(row.get(k, "")), styles["BodyText"]) for k in fieldnames])

            # ANCHO TOTAL DISPONIBLE (landscape)
            max_width = landscape(A4)[0] - 80
            col_count = len(fieldnames)
            col_width = max_width / col_count

            col_widths = [col_width] * col_count

            table = Table(table_data, colWidths=col_widths, repeatRows=1)

            # Estilos
            table.setStyle(TableStyle([
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5A5A5A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),

                # Cuerpo
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F1F1D4")),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),

                # Bordes y alineación
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                # Padding
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            story.append(table)

            # Render PDF
            doc.build(story)

            pdf_value = buffer.getvalue()
            buffer.close()

            response = HttpResponse(pdf_value, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.pdf"'
            return response

