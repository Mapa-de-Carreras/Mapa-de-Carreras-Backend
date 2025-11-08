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

    nombre = models.CharField(max_length=50)
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
    regimen = models.ForeignKey(
        "gestion_academica.ParametrosRegimen", on_delete=models.PROTECT, related_name="designaciones")
    cargo = models.ForeignKey(
        Cargo, on_delete=models.PROTECT, null=False, related_name="designaciones")

    observacion = models.TextField(blank=True, null=True)

    documento = models.ForeignKey("gestion_academica.Documento", on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name="designaciones")

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
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

    def clean(self):
        # Contamos las designaciones activas que ya tiene el docente
        # Excluimos la designación actual si ya existe (para casos de edición)
        designaciones_actuales = Designacion.objects.filter(
            docente=self.docente, fecha_fin__isnull=True
        ).exclude(pk=self.pk)

        # Obtenemos el máximo permitido por el régimen de esta designación
        max_permitido = self.regimen.max_asignaturas

        if designaciones_actuales.count() >= max_permitido:
            raise ValidationError(
                f'El docente {self.docente} ya ha alcanzado el límite de {max_permitido} asignaturas '
                f'para su régimen de {self.regimen.dedicacion.nombre}.'
            )
