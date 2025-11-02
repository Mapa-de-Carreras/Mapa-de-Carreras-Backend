from rest_framework import serializers
from gestion_academica import models
from .user_serializers import UsuarioSerializer

from django.contrib.auth import authenticate
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        usuario = authenticate(username=data['username'], password=data['password'])
        if usuario and usuario.is_active:
            return {'user': usuario}
        raise serializers.ValidationError("Nombre de usuario o contraseña inválidos")
    

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(
        help_text="El Refresh Token JWT para invalidar la sesión."
    )


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rol
        fields = ['id', 'nombre', 'description']


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


class CarreraCoordinacionSerializer(serializers.ModelSerializer):
    carrera = serializers.StringRelatedField(
        read_only=True
    )
    carrera_id = serializers.PrimaryKeyRelatedField(
        source="carrera",
        queryset=models.Carrera.objects.all(),
        write_only=True
    )

    coordinador = serializers.StringRelatedField(read_only=True)
    coordinador_id = serializers.PrimaryKeyRelatedField(
        source="coordinador",
        queryset=models.Coordinador.objects.all(),
        write_only=True
    )

    creado_por = UsuarioSerializer(read_only=True)
    creado_por_id = serializers.PrimaryKeyRelatedField(
        source="creado_por",
        queryset=models.Usuario.objects.all(),
        write_only=True
    )

    class Meta:
        model = models.CarreraCoordinacion
        fields = [
            'id', 'carrera', 'carrera_id', 'coordinador', 'coordinador_id',
            'fecha_inicio', 'fecha_fin', 'activo', 'creado_por', 'creado_por_id'
        ]


class CoordinadorSerializer(serializers.ModelSerializer):
    carreras_coordinadas = CarreraCoordinacionSerializer(
        source="carreracoordinacion_set",
        many=True,
        read_only=True
    )

    class Meta:
        model = models.Coordinador
        fields = [
            'id', 'legajo', 'nombre', 'apellido', 'email', 'celular',
            'carreras_coordinadas'
        ]
        read_only_fields = ['legajo', 'nombre', 'apellido', 'email', 'celular']