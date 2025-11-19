import csv
import io
from openpyxl import Workbook
from django.http import HttpResponse

from gestion_academica.models.M5_estadisticas_reportes import ExportLog
from django.contrib.auth import get_user_model

Usuario = get_user_model()


def generar_csv(nombre_archivo, campos, rows, usuario: Usuario, tipo_reporte, filtros):
    try:
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # cabeceras
        writer.writerow(campos)

        # filas
        for row in rows:
            fila = [row.get(c, "") for c in campos]
            writer.writerow(fila)

        ExportLog.objects.create(
            usuario=usuario,
            tipo_reporte=tipo_reporte,
            formato="CSV",
            filtros=filtros,
            exito=True
        )

        resp = HttpResponse(buffer.getvalue(), content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.csv"'
        return resp

    except Exception as e:
        ExportLog.objects.create(
            usuario=usuario,
            tipo_reporte=tipo_reporte,
            formato="CSV",
            filtros=filtros,
            exito=False,
            mensaje_error=str(e),
        )
        raise e


def generar_excel(nombre_archivo, campos, rows, usuario: Usuario, tipo_reporte, filtros):
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"

        ws.append(campos)

        for row in rows:
            ws.append([row.get(c, "") for c in campos])

        buffer = io.BytesIO()
        wb.save(buffer)

        ExportLog.objects.create(
            usuario=usuario,
            tipo_reporte=tipo_reporte,
            formato="XLSX",
            filtros=filtros,
            exito=True
        )

        resp = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        resp["Content-Disposition"] = f'attachment; filename="{nombre_archivo}.xlsx"'
        return resp

    except Exception as e:
        ExportLog.objects.create(
            usuario=usuario,
            tipo_reporte=tipo_reporte,
            formato="XLSX",
            filtros=filtros,
            exito=False,
            mensaje_error=str(e),
        )
        raise e
