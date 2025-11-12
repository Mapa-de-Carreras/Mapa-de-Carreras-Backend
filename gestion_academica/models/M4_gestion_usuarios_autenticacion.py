# gestion_academica/models/M4_gestion_usuarios_autenticacion.py

'''
MODULO 4: GESTIÓN DE USUARIOS Y AUTENTICACIÓN

Incluye las entidades Usuario, Rol, RolUsuario, 
Notificacion, UsuarioNotificacion, CarreraCoordinacion y Coordinador
'''

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.crypto import get_random_string
from .M1_gestion_academica import Carrera


class Usuario(AbstractUser):
    """Modelo base para todos los usuarios del sistema."""
    legajo = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    celular = models.CharField(max_length=50, blank=True, null=True)

    # definicion de la relacion muchos a muchos a traves del modelo puente
    roles = models.ManyToManyField(
        "Rol", through="RolUsuario", related_name="usuarios")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], name='uq_email_unico')
        ]

    # campos requeridos al crear un superusuario
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    def generate_verification_token(self):
        """Genera un token aleatorio para la verificación del email"""
        self.verification_token = get_random_string(64)
        self.save()

    def has_perm(self, perm, obj=None):
        """¿Tiene el usuario un permiso específico?"""
        # Solo si es superusuario.
        return self.is_superuser

    def has_module_perms(self, app_label):
        """¿Tiene el usuario permisos para ver la app `app_label`?"""
        # Solo si es superusuario.
        return self.is_superuser

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Rol(models.Model):
    """Tabla catálogo para los roles del sistema (Admin, Coordinador, Docente)."""
    nombre = models.CharField(max_length=20, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

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
    created_at = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name="coordinaciones_creadas")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=[
                                    'carrera', 'coordinador', 'fecha_inicio'], name='uq_carrera_coordinador_periodo')
        ]

    def __str__(self):
        return f"{self.coordinador} - {self.carrera} ({'activo' if self.activo else 'inactivo'})"


class Coordinador(models.Model):
    """
    Modelo para el Coordinador. Hereda todos los campos de Usuario
    y añade la relación con las carreras que coordina.
    """
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="coordinador"
    )
    carreras_coordinadas = models.ManyToManyField(
        "gestion_academica.Carrera", through=CarreraCoordinacion, related_name='coordinadores')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.usuario.last_name} {self.usuario.first_name}"
