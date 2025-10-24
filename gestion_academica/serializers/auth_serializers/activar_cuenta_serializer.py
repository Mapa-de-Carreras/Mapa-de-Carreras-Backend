from rest_framework import serializers
from gestion_academica import models
from django.core.cache import cache


class ActivarCuentaSerializer(serializers.Serializer):
    """
    Serializer para validar el código de activación de un nuevo usuario.
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, write_only=True)

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')

        # 1. Validar el usuario
        try:
            user = models.Usuario.objects.get(email=email)
        except models.Usuario.DoesNotExist:
            raise serializers.ValidationError({"email": "El correo electrónico no está registrado."})
        
        # 2. Verificar que la cuenta no esté ya activa
        if user.is_active:
             raise serializers.ValidationError({"detail": "Esta cuenta ya ha sido activada."})

        # 3. Validar el código de caché
        cache_key = f"verification_code_{email}"
        stored_code = cache.get(cache_key)

        if not stored_code:
            raise serializers.ValidationError({"code": "Código expirado. Por favor, solicita uno nuevo."})
        
        if str(stored_code) != code:
            raise serializers.ValidationError({"code": "Código incorrecto."})
        
        # Si todo está bien, guardamos el usuario para la vista y limpiamos caché
        data['user'] = user
        cache.delete(cache_key)
        
        return data