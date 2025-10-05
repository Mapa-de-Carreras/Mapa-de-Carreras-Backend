from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# Create your models here.

# --- ESTRUCTURA ACADÉMICA ---


class Instituto(models.Model):
    """Representa una unidad académica principal de la universidad."""
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)

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
    instituto = models.ForeignKey(Instituto, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Resolucion(models.Model):
    """Almacena los datos de una resolución oficial que aprueba un plan de estudios."""
    tipo = models.CharField(max_length=50)
    emisor = models.CharField(max_length=100)
    numero = models.IntegerField()
    anio = models.IntegerField()

    class Meta:
        unique_together = ("tipo", "emisor", "numero", "anio")

    def __str__(self):
        return f"{self.tipo}-{self.emisor} N°{self.numero}/{self.anio}"


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

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)

    anio = models.PositiveIntegerField(default=1)
    cuatrimestre = models.PositiveIntegerField(default=1)

    tipo_asignatura = models.CharField(
        max_length=20, choices=TIPO_ASIGNATURA_CHOICES)
    tipo_duracion = models.CharField(
        max_length=20, choices=TIPO_DURACION_CHOICES)
    horas_teoria = models.PositiveIntegerField(default=0)
    horas_practica = models.PositiveIntegerField(default=0)
    horas_semanales = models.PositiveIntegerField(default=0)
    horas_totales = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.horas_totales = self.horas_teoria + self.horas_practica
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class PlanDeEstudio(models.Model):
    """Define la estructura de un plan de estudios para una carrera."""
    fecha_inicio = models.DateField()
    esta_vigente = models.BooleanField(default=True)

    documento = models.FileField(upload_to="planes/", blank=True, null=True)

    resolucion = models.OneToOneField(Resolucion, on_delete=models.PROTECT)
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    asignaturas = models.ManyToManyField(Asignatura, through="PlanAsignatura")

    def __str__(self):
        return f"Plan {self.resolucion} ({self.carrera.nombre})"


class PlanAsignatura(models.Model):
    """Modelo 'puente' que conecta una Asignatura a un PlanDeEstudio específico."""
    plan_de_estudio = models.ForeignKey(
        PlanDeEstudio, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)

    class Meta:
        # Asegura que no se pueda añadir la misma asignatura dos veces al mismo plan
        unique_together = ("plan_de_estudio", "asignatura")

    def __str__(self):
        return f"{self.plan_de_estudio} - {self.asignatura}"


class Correlativa(models.Model):
    """Define una relación de prerrequisito entre dos asignaturas dentro de un mismo plan."""
    plan_asignatura = models.ForeignKey(
        PlanAsignatura, on_delete=models.CASCADE, related_name="correlativas_requeridas")
    correlativa_requerida = models.ForeignKey(
        PlanAsignatura, on_delete=models.CASCADE, related_name='es_requisito_para')

    class Meta:
        unique_together = ('plan_asignatura', 'correlativa_requerida')

    def clean(self):
        if self.plan_asignatura.plan_de_estudio != self.correlativa_requerida.plan_de_estudio:
            raise ValidationError(
                'Las correlativas deben pertenecer al mismo plan de estudios.')

    def __str__(self):
        return f"{self.plan_asignatura.asignatura.nombre} requiere {self.correlativa_requerida.asignatura.nombre}"


class Comision(models.Model):
    """Representa una comisión específica de una asignatura (ej: 'Comisión A, Turno Mañana')."""
    TURNO_CHOICES = [
        ('MANANA', 'Mañana'),
        ('TARDE', 'Tarde'),
        ('NOCHE', 'Noche'),
    ]

    nombre = models.CharField(max_length=50)  # por ejemplo: comision A
    turno = models.CharField(max_length=20, choices=TURNO_CHOICES)
    promocionable = models.BooleanField(default=False)
    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE, related_name="comisiones")

    def __str__(self):
        return f"{self.asignatura.nombre} - {self.nombre}"


# --- PERSONAL Y ROLES ---


class Modalidad(models.Model):
    """Tabla catálogo para las modalidades de los docentes (ej: Presencial)."""
    nombre = models.CharField(max_length=30)

    def __str__(self):
        return self.nombre


class Cargo(models.Model):
    """Tabla catálogo para los cargos docentes (ej: Titular, Adjunto)."""
    nombre = models.CharField(max_length=30)

    def __str__(self):
        return self.nombre


class Docente(models.Model):
    """Perfil que extiende el modelo User con datos específicos de un docente."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='docente')
    legajo = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    celular = models.CharField(max_length=50, blank=True, null=True)
    cargo = models.ForeignKey(
        Cargo, on_delete=models.SET_NULL, null=True, blank=True)
    modalidad = models.ForeignKey(
        Modalidad, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name()


class Coordinador(models.Model):
    """Perfil que extiende el modelo User para un coordinador, indicando qué carreras gestiona."""
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='coordinador')
    carreras = models.ManyToManyField(
        Carrera, blank=True, related_name='coordinadores')

    def __str__(self):
        return self.user.get_full_name()


class Dedicacion(models.Model):
    """Tabla catálogo para las dedicaciones docentes (ej: Simple, Exclusiva)."""
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


# --- REGLAS Y EVENTOS ---


class ParametrosRegimen(models.Model):
    """Define un conjunto de reglas laborales combinando una Modalidad y una Dedicacion."""
    modalidad = models.ForeignKey(Modalidad, on_delete=models.CASCADE)
    dedicacion = models.ForeignKey(Dedicacion, on_delete=models.CASCADE)

    horas_min_semanal = models.PositiveIntegerField()
    horas_max_semanal = models.PositiveIntegerField()
    horas_min_anual = models.PositiveIntegerField()
    horas_max_anual = models.PositiveIntegerField()
    max_asignaturas = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.modalidad} - {self.dedicacion}"


class Designacion(models.Model):
    """Modelo 'evento' que registra la asignación de un Docente a una Comisión."""
    TIPO_DESIGNACION_CHOICES = [
        ('TITULAR', 'Titular'),
        ('INTERINO', 'Interino'),
        ('SUPLENTE', 'Suplente'),
    ]

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    tipo_designacion = models.CharField(
        max_length=20, choices=TIPO_DESIGNACION_CHOICES)

    docente = models.ForeignKey(
        Docente, on_delete=models.CASCADE, related_name="designaciones")
    comision = models.ForeignKey(Comision, on_delete=models.CASCADE)
    regimen = models.ForeignKey(ParametrosRegimen, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.docente} en {self.comision}"
