# gestion_academica/serializers/M4_gestion_usuarios_autenticacion.py

from django.contrib.auth import authenticate
from rest_framework import serializers
from gestion_academica import models
from .user_serializers.usuario_serializer import UsuarioSerializer

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        usuario = authenticate(
            username=data['username'], password=data['password'])
        if usuario and usuario.is_active:
            return {'user': usuario}

        raise serializers.ValidationError(
            "Nombre de usuario o contraseña inválidos")


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(
        help_text="El Refresh Token JWT para invalidar la sesión."
    )


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rol
        fields = ['id', 'nombre', 'descripcion']


class RolUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RolUsuario
        fields = ['id', 'usuario', 'rol']


class NotificacionSerializer(serializers.ModelSerializer):
    creado_por = UsuarioSerializer(read_only=True)
    creado_por_id = serializers.PrimaryKeyRelatedField(
        source='creado_por',
        write_only=True,
        queryset=models.Usuario.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = models.Notificacion
        fields = ['id', 'titulo', 'mensaje', 'tipo',
                  'creado_por', 'creado_por_id', 'fecha_creacion']


class UsuarioNotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UsuarioNotificacion
        fields = ['id', 'usuario', 'notificacion', 'leida',
                  'fecha_leida', 'eliminado', 'created_at']
