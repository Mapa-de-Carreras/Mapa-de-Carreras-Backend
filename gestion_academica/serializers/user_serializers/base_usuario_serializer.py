from datetime import date
from rest_framework import serializers
from gestion_academica import models

# --- 1. CREAMOS LA CLASE DE USUARIO BASE CON LA LÓGICA REUTILIZABLE ---

class BaseUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer base que contiene la lógica compartida de validación
    y actualización para todos los serializers de Usuario.
    """

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

        # 2. Validaciones de unicidad (Que exista solo 1) (Email, Username, Celular)
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
        Maneja la actualización de datos.
        """
        
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