
# gestion_academica/models/M5_estadisticas_reportes.py
"""
MODULO 5: ESTADÍSTICAS Y REPORTES

En este módulo NO se crean nuevas entidades de dominio para docentes o designaciones,
se reutilizan las de:

- M1_gestion_academica: Carrera, Asignatura, etc.
- M2_gestion_docentes: Docente, Dedicacion, Modalidad, ParametrosRegimen
- M3_designaciones_docentes: Designacion
- M4_gestion_usuarios_autenticacion: Usuario, Coordinador, CarreraCoordinacion

Este archivo define solo el modelo necesario para:
- RF [5.3.0] Exportar Datos: registrar las exportaciones realizadas.
"""

from django.db import models
from django.utils import timezone

from .M4_gestion_usuarios_autenticacion import Usuario


TIPO_REPORTE_CHOICES = [
    ("DOCENTES_POR_DEDICACION", "Docentes por dedicación"),
    ("DOCENTES_POR_MODALIDAD", "Docentes por modalidad"),
    ("HORAS_POR_DOCENTE", "Horas frente a alumnos por docente"),
    ("DESIGNACIONES_CARRERA", "Designaciones por asignatura/carrera"),
    ("HISTORIAL_DOCENTE", "Evolución histórica de designaciones de un docente"),
]

FORMATO_REPORTE_CHOICES = [
    ("CSV", "Archivo CSV"),
    ("XLSX", "Archivo Excel"),
    ("PDF", "Archivo PDF"),
]


class ExportLog(models.Model):
    """
    Registra las acciones de exportación de datos estadísticos.

    Cumple con la postcondición de RF [5.3.0]:
    "El sistema registra la acción de exportación (usuario, fecha, tipo de datos, formato)."

    Campos:
    - usuario: coordinador o usuario que pidió la exportación.
    - tipo_reporte: qué conjunto de datos se exportó.
    - formato: CSV, XLSX, PDF.
    - filtros: JSON con los filtros aplicados (carrera, periodo, dedicación, etc.).
    - generado_en: fecha/hora de la exportación.
    - exito: si la exportación fue exitosa o no.
    - mensaje_error: detalle del error si falló.
    """

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exportaciones_estadisticas",
        help_text="Usuario (coordinador) que realizó la exportación.",
    )

    tipo_reporte = models.CharField(
        max_length=50,
        choices=TIPO_REPORTE_CHOICES,
        help_text="Tipo de reporte exportado (ej: docentes por dedicación).",
    )

    formato = models.CharField(
        max_length=10,
        choices=FORMATO_REPORTE_CHOICES,
        help_text="Formato de exportación (CSV, XLSX, PDF).",
    )

    filtros = models.JSONField(
        null=True,
        blank=True,
        help_text="Filtros aplicados (carrera, periodo, rango fechas, dedicación, modalidad, etc.).",
    )

    generado_en = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en la que se generó el archivo.",
    )

    exito = models.BooleanField(
        default=True,
        help_text="Indica si la exportación fue exitosa.",
    )

    mensaje_error = models.TextField(
        null=True,
        blank=True,
        help_text="Detalle del error en caso de fallar la generación del archivo.",
    )

    class Meta:
        verbose_name = "Registro de Exportación de Estadísticas"
        verbose_name_plural = "Registros de Exportación de Estadísticas"
        ordering = ["-generado_en"]

    def __str__(self):
        estado = "OK" if self.exito else "ERROR"
        return f"[{estado}] {self.tipo_reporte} en {self.formato} - {self.generado_en:%Y-%m-%d %H:%M}"
