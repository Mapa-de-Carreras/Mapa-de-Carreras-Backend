# gestion_academica/models/M3_designaciones_docentes.py

'''
MODULO 3: DESIGNACIONES DOCENTES

Incluye las entidades Desigacion, Comision y Cargo
'''

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


class Comision(models.Model):
    """Representa una comisión específica de una asignatura (ej: 'Comisión A, Turno Mañana')."""
    TURNO_CHOICES = [
        ('MATUTINO', 'Matutino'),
        ('VESPERTINO', 'Vespertino'),
    ]

    nombre = models.CharField(max_length=50)  # por ejemplo: comision A
    turno = models.CharField(
        max_length=20, choices=TURNO_CHOICES, db_index=True)
    promocionable = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    asignatura = models.ForeignKey(
        "gestion_academica.Asignatura", on_delete=models.CASCADE, related_name="comisiones")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asignatura", "nombre"], name="uq_comision_asignatura_nombre")
        ]

    def __str__(self):
        return f"{self.asignatura.nombre} - {self.nombre}"


class Cargo(models.Model):
    """Tabla catálogo para los cargos docentes (ej: Titular, Adjunto)."""
    nombre = models.CharField(max_length=30, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Designacion(models.Model):
    """Modelo 'evento' que registra la asignación de un Docente a una Comisión."""
    TIPO_DESIGNACION_CHOICES = [
        ('TEORICO', 'Teorico'),
        ('PRACTICO', 'Practico'),
        ('TEORICO + PRACTICO', 'Teorico + Practico'),
    ]

    fecha_inicio = models.DateField(db_index=True)
    fecha_fin = models.DateField(null=True, blank=True, db_index=True)
    tipo_designacion = models.CharField(
        max_length=20, choices=TIPO_DESIGNACION_CHOICES)

    docente = models.ForeignKey(
        "gestion_academica.Docente", on_delete=models.CASCADE, related_name="designaciones")
    comision = models.ForeignKey(
        Comision, on_delete=models.PROTECT, related_name="designaciones")

    dedicacion = models.ForeignKey("gestion_academica.Dedicacion",
                                   on_delete=models.PROTECT, null=True, blank=True, related_name="designaciones")

    modalidad = models.ForeignKey(
        "gestion_academica.Modalidad", on_delete=models.PROTECT, null=True, blank=True, related_name="designaciones"
    )

    regimen = models.ForeignKey("gestion_academica.ParametrosRegimen",
                                on_delete=models.PROTECT, null=True, blank=True, related_name="designaciones")

    cargo = models.ForeignKey(
        Cargo, on_delete=models.PROTECT, null=False, related_name="designaciones")

    observacion = models.TextField(blank=True, null=True)

    documento = models.ForeignKey("gestion_academica.Documento", on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="designaciones")

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='designaciones_creadas',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=[
                                    'docente', 'comision', 'fecha_inicio', 'fecha_fin'], name='uq_designacion_exact'),
        ]

    def __str__(self):
        return f"{self.docente} en {self.comision}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        return None

    def excede_maximo(self):
        """
        Retorna True si las designaciones activas del docente
        igualan o superan el max permitidas por el regimen.
        """
        regimen = getattr(self, "regimen", None)
        if not regimen:
            return False
        designaciones_actuales = Designacion.objects.filter(
            docente=self.docente, fecha_fin__isnull=True
        ).exclude(pk=self.pk)
        return designaciones_actuales.count() >= regimen.max_asignaturas
