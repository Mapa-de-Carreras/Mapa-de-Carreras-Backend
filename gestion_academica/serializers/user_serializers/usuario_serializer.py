from rest_framework import serializers
from gestion_academica import models
from .base_usuario_serializer import BaseUsuarioSerializer
from ..validators import validar_nueva_contraseña

class UsuarioSerializer(BaseUsuarioSerializer):
    """
    Serializer para el ADMIN. Puede ver y editar todos los campos
    y también crear usuarios.
    """
    roles = serializers.PrimaryKeyRelatedField(
        queryset=models.Rol.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )

    class Meta:
        model = models.Usuario
        # El Admin puede ver y editar todo
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active',
            'password', 'password2', 'legajo', 'fecha_nacimiento', 
            'celular', 'roles'
        ]
        extra_kwargs = {
            # Hacemos que la contraseña no sea requerida en PATCH
            'password': {'required': False}, 
            'password2': {'required': False},
            'fecha_nacimiento': {'required': True} # Sigue siendo req. para crear
        }

    def validate(self, data):
        """
        Validación de 'create' (contraseñas coinciden y complejidad).
        """
        # 1. Llama a la validación del padre (BaseUsuarioSerializer)
        data = super().validate(data)
        # --- 2. USA LA LÓGICA CENTRALIZADA ---
        validar_nueva_contraseña(data['password'], data['password2'])
        return data

    def create(self, validated_data):
        roles_data = validated_data.pop('roles', [])
        validated_data.pop('old_password', None)
        validated_data.pop('password2', None)
    
        usuario = models.Usuario.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            legajo=validated_data['legajo'],
            celular=validated_data['celular'],
            fecha_nacimiento=validated_data.get('fecha_nacimiento', None),
            is_active=False
        )
        
        for rol in roles_data:
            models.RolUsuario.objects.create(usuario=usuario, rol=rol)
            
        return usuario