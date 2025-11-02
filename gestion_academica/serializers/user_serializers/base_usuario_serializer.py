from datetime import date
from rest_framework import serializers
from gestion_academica import models
import re

# --- 1. CREAMOS LA CLASE DE USUARIO BASE CON LA LÓGICA REUTILIZABLE ---

class BaseUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer base que contiene la lógica compartida de validación
    y actualización para todos los serializers de Usuario.
    """
    # Definimos los campos de contraseña aquí para que ambos herederos los tengan
    old_password = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        """ Validaciones """
        
        # self.instance es el usuario que se está actualizando.
        # En la creación (create), self.instance es None.
        instance = self.instance
        
        # 1. Validación de edad
        if 'fecha_nacimiento' in data and data['fecha_nacimiento']:
            birthdate = data['fecha_nacimiento']
            today = date.today()
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            
            if age < 18:
                raise serializers.ValidationError({
                    "fecha_nacimiento": "Debes tener al menos 18 años."
                })
        
        # 2. Validación de contraseña (si se intenta cambiar)
        if 'password' in data and data['password']:
            password = data['password']
            if len(password) < 8:
                raise serializers.ValidationError({"password": "La contraseña debe tener al menos 8 caracteres."})
            if not re.search(r'[A-Z]', password):
                raise serializers.ValidationError({"password": "La contraseña debe contener al menos una letra mayúscula."})
            if not re.search(r'[0-9]', password):
                raise serializers.ValidationError({"password": "La contraseña debe contener al menos un número."})
            
            # 2a. Validar contraseña actual (solo en actualizaciones)
            if instance: # Si es un update (no un create)
                if not 'old_password' in data:
                    raise serializers.ValidationError({"old_password": "Debe proporcionar la contraseña actual."})
                if not instance.check_password(data['old_password']):
                    raise serializers.ValidationError({"old_password": "La contraseña actual es incorrecta."})
            
            # 2b. Validar que las nuevas coincidan
            if 'password2' not in data or data['password'] != data['password2']:
                raise serializers.ValidationError({"password": "Las nuevas contraseñas no coinciden."})

        # 3. Validaciones de unicidad (Que exista solo 1) (Email, Username, Celular)
        email = data.get('email', None)
        username = data.get('username', None)
        celular = data.get('celular', None)
        
        current_pk = getattr(instance, 'pk', None)

        if email and models.Usuario.objects.exclude(pk=current_pk).filter(email=email).exists():
            raise serializers.ValidationError({"email": "El correo electrónico ya está en uso."})

        if username and models.Usuario.objects.exclude(pk=current_pk).filter(username=username).exists():
            raise serializers.ValidationError({"username": "El nombre de usuario ya está en uso."})

        if celular and models.Usuario.objects.exclude(pk=current_pk).filter(celular=celular).exists():
            raise serializers.ValidationError({"celular": "El número de celular ya está en uso."})
        
        return data
    
    def update(self, instance, validated_data):
        """
        Maneja la actualización de contraseña y otros campos.
        """
        # Maneja la actualización de contraseña si está presente
        if 'password' in validated_data:
            instance.set_password(validated_data.pop('password'))

        # Remueve campos de contraseña que no van en el modelo
        validated_data.pop('old_password', None)
        validated_data.pop('password2', None)
        
        # Actualiza los campos restantes (first_name, email, etc.)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

    def update_password_without_old(self, instance, validated_data):
        """ Método para resetear contraseña (usado por Admin/Recuperación) """
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
            instance.save()
        return instance