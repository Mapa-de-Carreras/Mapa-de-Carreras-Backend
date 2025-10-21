# gestion_academica/serializers/M4_gestion_usuarios_autenticacion.py

from datetime import date
from rest_framework import serializers
from gestion_academica import models
import re


class UsuarioSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=False)  # password2 solo se necesita en la creación
    password = serializers.CharField(write_only=True, required=False)   # password es opcional en la actualización
    old_password = serializers.CharField(write_only=True, required=False)  # Para validar contraseña actual

    class Meta:
        model = models.Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'is_staff','password', 'old_password','password2', 'legajo', 'fecha_nacimiento', 'celular'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # No es obligatorio en la actualización
            'password2': {'write_only': True, 'required': False},  # No es obligatorio en la actualización
            'fecha_nacimiento': {'required': True}
        }

    def validate(self, data):
        if self.instance is None and 'fecha_nacimiento' in data:
            birthdate = data['fecha_nacimiento']
            today = date.today()
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            
            if age < 18:
                raise serializers.ValidationError({
                    "fecha_nacimiento": "Debes tener al menos 18 años para registrarte."
                })
                
        if 'password' in data and data['password']:
            password = data['password']
            
            # Longitud mínima
            if len(password) < 8:
                raise serializers.ValidationError({
                    "password": "La contraseña debe tener al menos 8 caracteres."
                })
            
            # Al menos una mayúscula
            if not re.search(r'[A-Z]', password):
                raise serializers.ValidationError({
                    "password": "La contraseña debe contener al menos una letra mayúscula."
                })
            
            # Al menos un número
            if not re.search(r'[0-9]', password):
                raise serializers.ValidationError({
                    "password": "La contraseña debe contener al menos un número."
                })       

        # Validación para creación de usuario
        if self.instance is None:  # Es una creación
            if 'password' in data and 'password2' in data:
                if data['password'] != data['password2']:
                    raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        
        # Validación para cambio de contraseña
        elif 'password' in data:  # Es una actualización y se intenta cambiar la contraseña
            if not 'old_password' in data:
                raise serializers.ValidationError({"old_password": "Debe proporcionar la contraseña actual."})
            
            if not self.instance.check_password(data['old_password']):
                raise serializers.ValidationError({"old_password": "La contraseña actual es incorrecta."})

        email = data.get('email', None)
        username = data.get('username', None)
        celular = data.get('celular', None)

        # Validaciones de unicidad excluyendo la instancia actual
        if email and models.Usuario.objects.exclude(pk=getattr(self.instance, 'pk', None)).filter(email=email).exists():
            raise serializers.ValidationError({"email": "El correo electrónico ya está en uso."})

        if username and models.Usuario.objects.exclude(pk=getattr(self.instance, 'pk', None)).filter(username=username).exists():
            raise serializers.ValidationError({"username": "El nombre de usuario ya está en uso."})

        if celular and models.Usuario.objects.exclude(pk=getattr(self.instance, 'pk', None)).filter(celular=celular).exists():
            raise serializers.ValidationError({"celular": "El número de celular ya está en uso."})
        return data
    
    def create(self, validated_data):
        # Extrae los datos de la contraseña
        validated_data.pop('old_password', None)
        validated_data.pop('password2', None)
    
        # Crea el usuario y asocia la dirección creada
        usuario = models.Usuario.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            legajo=validated_data['legajo'],
            celular=validated_data['celular'],
            fecha_nacimiento = validated_data.get('fecha_nacimiento', None),
        )
        return usuario
            
    def update(self, instance, validated_data):
        # Maneja la actualización de contraseña si está presente
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))

        # Remueve campos que no queremos actualizar
        validated_data.pop('old_password', None)
        validated_data.pop('password2', None)
        validated_data.pop('fecha_nacimiento', None)  # Asegura que no se actualice la fecha de nacimiento
        
        # Actualiza los campos restantes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
    
    def update_password_without_old(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
            instance.save()
        return instance

    def obtener_id(self, validated_data):
        email = validated_data['email']
        try:
            usuario = models.Usuario.objects.get(email=email)
            return {"id": usuario.id}
        except models.Usuario.DoesNotExist:
            raise serializers.ValidationError({"email": "No se encontró un usuario con este correo electrónico"})
        

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