# gestion_academica/models/M1_gestion_academica.py

'''
MODULO 1: GESTIÓN ACADÉMICA

Incluye las entidades para Instituto, Carrera, PlanesDeEstudio, 
Asignatura, PlanAsignatura y Correlativa.
'''

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


class Instituto(models.Model):
    """Representa una unidad académica principal de la universidad."""
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Carrera(models.Model):
    """Modela una carrera universitaria, con su nivel y a qué instituto pertenece."""
    NIVEL_CHOICES = [
        ("TECNICATURA", "Tecnicatura"),
        ("DIPLOMATURA", "Diplomatura"),
        ("PREGRADO", "Pregrado"),
        ("GRADO", "Grado"),
        ("POSGRADO", "Posgrado"),
        ("MAESTRIA", "Maestria")
    ]

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES)
    esta_vigente = models.BooleanField(default=True)
    instituto = models.ForeignKey(
        Instituto, on_delete=models.PROTECT, related_name="carreras")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Asignatura(models.Model):
    """Representa una materia o asignatura, con su carga horaria y características."""
    TIPO_ASIGNATURA_CHOICES = [
        ('OBLIGATORIA', 'Obligatoria'),
        ('OPTATIVA', 'Optativa'),
    ]
    TIPO_DURACION_CHOICES = [
        ('ANUAL', 'Anual'),
        ('CUATRIMESTRAL', 'Cuatrimestral'),
    ]

    codigo = models.CharField(max_length=20, unique=True, db_index=True)
    nombre = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    cuatrimestre = models.PositiveIntegerField(default=1)

    tipo_asignatura = models.CharField(
        max_length=20, choices=TIPO_ASIGNATURA_CHOICES)
    tipo_duracion = models.CharField(
        max_length=20, choices=TIPO_DURACION_CHOICES)
    horas_teoria = models.PositiveIntegerField(default=0)
    horas_practica = models.PositiveIntegerField(default=0)
    horas_semanales = models.PositiveIntegerField(default=0)
    horas_totales = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.horas_totales = self.horas_teoria + self.horas_practica
        super().save(*args, **kwargs)

    def clean(self):
        if self.horas_totales != self.horas_teoria + self.horas_practica:
            raise ValidationError(
                "horas_totales debe ser la suma de teoria + practica")

    def __str__(self):
        return self.nombre


class Documento(models.Model):
    """
    Representa un documento administrativo o normativo emitido por la institución.
    """
    tipo = models.CharField(max_length=30, blank=True, null=True)
    emisor = models.CharField(max_length=200, blank=True, null=True)
    numero = models.CharField(max_length=50, blank=True, null=True)
    anio = models.PositiveIntegerField(blank=True, null=True)
    # tambien se añade un atributo para el propio documento
    archivo = models.FileField(upload_to="documentos/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "emisor", "numero", "anio"], name="uq_documento_identificador"
            )
        ]
        ordering = ["-anio", "emisor", "numero"]

    def __str__(self):
        return f"{self.tipo} {self.emisor} N°{self.numero}/{self.anio}"


class PlanDeEstudio(models.Model):
    """Define la estructura de un plan de estudios para una carrera."""
    fecha_inicio = models.DateField()
    esta_vigente = models.BooleanField(default=True)

    documento = models.ForeignKey(
        Documento, on_delete=models.SET_NULL, blank=True, null=True, related_name="planes")

    # mantener FK a carrera (pero puede ser nullable si prefiere el flujo: crear plan -> asignaturas -> asociar carrera)
    carrera = models.ForeignKey(
        Carrera, on_delete=models.PROTECT, related_name="planes", null=True, blank=True)
    asignaturas = models.ManyToManyField(
        Asignatura, through="PlanAsignatura", related_name="planes_de_estudio")

    # quien creó el plan (coordinador/usuario)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="planes_creados")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        carrera_nombre = self.carrera.nombre if self.carrera else "Sin carrera"
        return f"Plan {self.documento} ({carrera_nombre})"

    def clean(self):
        # regla: si se asocia carrera, debe tener al menos 1 asignatura
        if self.carrera_id:
            if not self.pk:
                # objeto nuevo: no se puede validar M2M aquí
                return
            if not PlanAsignatura.objects.filter(plan_de_estudio=self).exists():
                raise ValidationError(
                    "Un plan asociado a una carrera debe contener al menos una asignatura.")


class PlanAsignatura(models.Model):
    """Modelo puente que conecta una Asignatura a un PlanDeEstudio específico."""
    plan_de_estudio = models.ForeignKey(
        PlanDeEstudio, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    anio = models.PositiveIntegerField(null=False, default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan_de_estudio", "asignatura"], name="uq_plan_asignatura")
        ]
        indexes = [
            models.Index(fields=["plan_de_estudio", "asignatura"]),
        ]

    def __str__(self):
        return f"{self.plan_de_estudio} - {self.asignatura} (año {self.anio})"


class Correlativa(models.Model):
    """Define una relación de prerrequisito entre dos asignaturas dentro de un mismo plan."""
    plan_asignatura = models.ForeignKey(
        PlanAsignatura, on_delete=models.CASCADE, related_name="correlativas_requeridas")
    correlativa_requerida = models.ForeignKey(
        PlanAsignatura, on_delete=models.CASCADE, related_name='es_requisito_para')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['plan_asignatura', 'correlativa_requerida'], name='uq_correlativa')
        ]

    def clean(self):
        if self.plan_asignatura.plan_de_estudio != self.correlativa_requerida.plan_de_estudio:
            raise ValidationError(
                'Las correlativas deben pertenecer al mismo plan de estudios.')

        if self.plan_asignatura == self.correlativa_requerida:
            raise ValidationError(
                'Una asignatura no puede ser correlativa de sí misma.')

        origen_anio = getattr(self.plan_asignatura, 'anio', None)
        requerida_anio = getattr(self.correlativa_requerida, 'anio', None)

        asignatura_origen = self.plan_asignatura.asignatura
        asignatura_requerida = self.correlativa_requerida.asignatura

        if origen_anio is not None and requerida_anio is not None:
            if origen_anio == requerida_anio and asignatura_origen.cuatrimestre == asignatura_requerida.cuatrimestre:
                raise ValidationError(
                    'No se pueden establecer correlativas entre asignaturas del mismo año y cuatrimestre.'
                )

    def __str__(self):
        return f"{self.plan_asignatura.asignatura.nombre} requiere {self.correlativa_requerida.asignatura.nombre}"
