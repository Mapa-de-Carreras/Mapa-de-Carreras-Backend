# gestion_academica/models/M4_gestion_usuarios_autenticacion.py

'''
MODULO 4: GESTIÓN DE USUARIOS Y AUTENTICACIÓN

Incluye las entidades UsuarioManager, Usuario, Rol, RolUsuario, 
Notificacion, UsuarioNotificacion, CarreraCoordinacion y Coordinador
'''

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from .M1_gestion_academica import Carrera


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
        return f"{self.apellido} {self.nombre}"


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
        ("ADVERTENCIA", "Advertencia"),
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
        "gestion_academica.Carrera", through=CarreraCoordinacion, related_name='coordinadores')

    def __str__(self):
        return f"{self.apellido} {self.nombre}"
