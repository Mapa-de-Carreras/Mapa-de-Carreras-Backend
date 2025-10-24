import re
from rest_framework import serializers
from gestion_academica import models
from django.core.cache import cache

class RestablecerContraseñaSerializer(serializers.Serializer):
    """
    Serializer para validar el código de reseteo y la nueva contraseña.
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, write_only=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')
        password = data.get('password')
        password2 = data.get('password2')

        # 1. Validar el usuario
        try:
            user = models.Usuario.objects.get(email=email)
            # Guardamos el usuario en 'data' para pasarlo a la vista
            data['user'] = user
        except models.Usuario.DoesNotExist:
            raise serializers.ValidationError({"email": "El correo electrónico no está registrado."})

        # 2. Validar el código de caché
        cache_key = f"verification_code_{email}"
        stored_code = cache.get(cache_key)

        if not stored_code:
            raise serializers.ValidationError({"code": "Código expirado. Por favor, solicita uno nuevo."})
        
        if str(stored_code) != code:
            raise serializers.ValidationError({"code": "Código incorrecto."})

        # 3. Validar contraseñas
        if password != password2:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        # 4. Validar complejidad de la contraseña
        if len(password) < 8:
            raise serializers.ValidationError({"password": "La contraseña debe tener al menos 8 caracteres."})
        if not re.search(r'[A-Z]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos una letra mayúscula."})
        if not re.search(r'[0-9]', password):
            raise serializers.ValidationError({"password": "La contraseña debe contener al menos un número."})
        
        # Si todo está bien, limpiamos el código de la caché
        cache.delete(cache_key)
        
        return data