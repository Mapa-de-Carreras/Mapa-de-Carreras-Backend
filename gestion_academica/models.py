from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils import timezone

# Create your models here.

# --- ESTRUCTURA ACADÉMICA ---


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


class Resolucion(models.Model):
    """Almacena los datos de una resolución oficial que aprueba un plan de estudios."""
    tipo = models.CharField(max_length=50)
    emisor = models.CharField(max_length=100)
    numero = models.IntegerField()
    anio = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tipo", "emisor", "numero", "anio"], name="uq_resolucion")
        ]

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

    codigo = models.CharField(max_length=20, unique=True, db_index=True)
    nombre = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

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


class PlanDeEstudio(models.Model):
    """Define la estructura de un plan de estudios para una carrera."""
    fecha_inicio = models.DateField()
    esta_vigente = models.BooleanField(default=True)

    documento = models.FileField(upload_to="planes/", blank=True, null=True)

    resolucion = models.ForeignKey(
        Resolucion, on_delete=models.PROTECT, related_name="plan")
    # mantener FK a carrera (pero puede ser nullable si prefiere el flujo: crear plan -> asignaturas -> asociar carrera)
    carrera = models.ForeignKey(
        Carrera, on_delete=models.PROTECT, related_name="planes", null=True, blank=True)
    asignaturas = models.ManyToManyField(
        Asignatura, through="PlanAsignatura", related_name="planes_de_estudio")

    # quien creó el plan (coordinador/usuario)
    creado_por = models.ForeignKey(
        "Usuario", on_delete=models.SET_NULL, null=True, blank=True, related_name="planes_creados")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        carrera_nombre = self.carrera.nombre if self.carrera else "Sin carrera"
        return f"Plan {self.resolucion} ({carrera_nombre})"

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
        return f"{self.plan_de_estudio} - {self.asignatura}"


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

        asignatura_origen = self.plan_asignatura.asignatura
        asignatura_requerida = self.correlativa_requerida.asignatura

        if asignatura_origen.anio == asignatura_requerida.anio and asignatura_origen.cuatrimestre == asignatura_requerida.cuatrimestre:
            raise ValidationError(
                'No se pueden establecer correlativas entre asignaturas del mismo año y cuatrimestre.'
            )

    def __str__(self):
        return f"{self.plan_asignatura.asignatura.nombre} requiere {self.correlativa_requerida.asignatura.nombre}"


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
        Asignatura, on_delete=models.CASCADE, related_name="comisiones")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["asignatura", "nombre"], name="uq_comision_asignatura_nombre")
        ]

    def __str__(self):
        return f"{self.asignatura.nombre} - {self.nombre}"


# --- PERSONAL Y ROLES ---

class UsuarioManager(BaseUserManager):
    def create_user(self, legajo, password=None, **extra_fields):
        if not legajo:
            raise ValueError('El legajo es obligatorio')
        user = self.model(legajo=legajo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, legajo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        user = self.create_user(legajo, password, **extra_fields)
        admin_rol, _ = Rol.objects.get_or_create(nombre='Administrador')
        user.roles.add(admin_rol)
        return user


class Usuario(AbstractBaseUser):
    """Modelo base para todos los usuarios del sistema."""
    legajo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=30)
    apellido = models.CharField(max_length=30)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True)
    celular = models.CharField(max_length=50, blank=True, null=True)

    # campos para el panel de admin
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # manager del modelo
    objects = UsuarioManager()

    # definicion de la relacion muchos a muchos a traves del modelo puente
    roles = models.ManyToManyField(
        "Rol", through="RolUsuario", related_name="usuarios")

    USERNAME_FIELD = "legajo"  # este es el campo de inicio de sesion
    # campos requeridos al crear un superusuario
    REQUIRED_FIELDS = ["nombre", "apellido", "email"]

    def has_perm(self, perm, obj=None):
        """¿Tiene el usuario un permiso específico?"""
        # Solo si es superusuario.
        return self.is_superuser

    def has_module_perms(self, app_label):
        """¿Tiene el usuario permisos para ver la app `app_label`?"""
        # Solo si es superusuario.
        return self.is_superuser

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class Rol(models.Model):
    """Tabla catálogo para los roles del sistema (Admin, Coordinador, Docente)."""
    nombre = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.nombre


class RolUsuario(models.Model):
    """Modelo puente que conecta un Usuario con sus Roles."""
    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="roles_usuario")
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE,
                            related_name="roles_usuario")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "rol"], name="uq_usuario_rol")
        ]


class Notificacion(models.Model):
    """Contenido de una notificación que puede enviarse a varios usuarios."""
    TIPO_CHOICES = [
        ("INFO", "Info"),
        ("ALERTA", "Alerta"),
        ("ADVENTENCIA", "Advertencia"),
        ("SISTEMA", "Sistema")
    ]

    titulo = models.CharField(max_length=120)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, blank=True,
                            null=True, choices=TIPO_CHOICES)
    creado_por = models.ForeignKey("Usuario", on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="notificaciones_creadas")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.fecha_creacion.date()})"


class UsuarioNotificacion(models.Model):
    """Puente Usuario <-> Notificacion que guarda el estado por destinatario."""
    usuario = models.ForeignKey(
        "Usuario", on_delete=models.CASCADE, related_name="usuario_notificaciones")
    notificacion = models.ForeignKey(
        Notificacion, on_delete=models.CASCADE, related_name="destinatarios")
    leida = models.BooleanField(default=False)
    fecha_leida = models.DateTimeField(null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "notificacion"], name="uq_usuario_notificacion")
        ]

    def marcar_leida(self):
        if not self.leida:
            self.leida = True
            self.fecha_leida = timezone.now()
            self.save()


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


class Cargo(models.Model):
    """Tabla catálogo para los cargos docentes (ej: Titular, Adjunto)."""
    nombre = models.CharField(max_length=30, unique=True)

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
        "Dedicacion", on_delete=models.SET_NULL, null=True, blank=True, related_name="docentes")
    cantidad_materias = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.apellido} {self.nombre}"


class CarreraCoordinacion(models.Model):
    """
    Modelo para registrar historia de coordinaciones de carrera.
    Mantiene fecha inicio/fin, activo y quien asignó/guardó la relación.
    """
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)
    coordinador = models.ForeignKey("Coordinador", on_delete=models.CASCADE)
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="coordinaciones_creadas")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=[
                                    'carrera', 'coordinador', 'fecha_inicio'], name='uq_carrera_coordinador_periodo')
        ]

    def __str__(self):
        return f"{self.coordinador} - {self.carrera} ({'activo' if self.activo else 'inactivo'})"


class Coordinador(Usuario):
    """
    Modelo para el Coordinador. Hereda todos los campos de Usuario
    y añade la relación con las carreras que coordina.
    """
    carreras_coordinadas = models.ManyToManyField(
        Carrera, through=CarreraCoordinacion, related_name='coordinadores')

    def __str__(self):
        return f"{self.apellido} {self.nombre}"


class Dedicacion(models.Model):
    """Tabla catálogo para las dedicaciones docentes (ej: Simple, Exclusiva)."""
    nombre = models.CharField(max_length=50, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


# --- REGLAS Y EVENTOS ---


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
        Docente, on_delete=models.CASCADE, related_name="designaciones")
    comision = models.ForeignKey(
        Comision, on_delete=models.PROTECT, related_name="designaciones")
    regimen = models.ForeignKey(
        ParametrosRegimen, on_delete=models.PROTECT, related_name="designaciones")
    cargo = models.ForeignKey(
        Cargo, on_delete=models.PROTECT, null=False, related_name="designaciones")

    observacion = models.TextField(blank=True, null=True)
    documento = models.FileField(
        upload_to="designaciones/", blank=True, null=True)

    creado_por = models.ForeignKey(
        Usuario,
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
