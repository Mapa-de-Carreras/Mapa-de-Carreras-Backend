# gestion_academica/models/M2_gestion_docentes.py

'''
MODULO 2: GESTIÓN DE DOCENTES

Incluye las entidades para Docente, Modalidad, 
Caracter, Dedicacion y ParametrosRegimen.
'''

from django.db import models
from django.core.exceptions import ValidationError
from .M4_gestion_usuarios_autenticacion import Usuario


class Caracter(models.Model):
    """Tabla catálogo para el carácter de la designación (ej: Regular, Interino)."""
    nombre = models.CharField(max_length=30, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Modalidad(models.Model):
    """Tabla catálogo para las modalidades de los docentes (ej: Presencial)."""
    nombre = models.CharField(max_length=30, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Dedicacion(models.Model):
    """Tabla catálogo para las dedicaciones docentes (ej: Simple, Exclusiva)."""
    nombre = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Docente(Usuario):
    """
    Modelo para el Docente. Hereda todos los campos de Usuario
    y añade relaciones específicas de su rol.
    """
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.SET_NULL, null=True, blank=True, related_name="docentes")
    caracter = models.ForeignKey(
        Caracter, on_delete=models.SET_NULL, null=True, blank=True, related_name="docentes")
    dedicacion = models.ForeignKey(
        Dedicacion, on_delete=models.SET_NULL, null=True, blank=True, related_name="docentes")
    cantidad_materias = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.apellido} {self.nombre}"


class ParametrosRegimen(models.Model):
    """Define un conjunto de reglas laborales combinando una Modalidad y una Dedicacion."""
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.CASCADE, related_name="parametros_regimen")
    dedicacion = models.ForeignKey(
        Dedicacion, on_delete=models.CASCADE, related_name="parametros_regimen")

    horas_max_frente_alumnos = models.PositiveIntegerField()
    horas_min_frente_alumnos = models.PositiveIntegerField()
    horas_max_actual = models.PositiveIntegerField()
    horas_min_actual = models.PositiveIntegerField()
    max_asignaturas = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('modalidad', 'dedicacion'), name='uq_parametros_regimen')
        ]

    def clean(self):
        if self.dedicacion.nombre.lower() == 'simple' and self.max_asignaturas > 2:
            raise ValidationError(
                'Para dedicación Simple, el máximo de asignaturas no puede ser mayor a 2.'
            )
        if self.dedicacion.nombre.lower() in ['exclusiva', 'semiexclusiva'] and self.max_asignaturas > 3:
            raise ValidationError(
                'Para dedicación Exclusiva o Semiexclusiva, el máximo de asignaturas no puede ser mayor a 3.'
            )

    def __str__(self):
        return f"{self.modalidad} - {self.dedicacion}"
