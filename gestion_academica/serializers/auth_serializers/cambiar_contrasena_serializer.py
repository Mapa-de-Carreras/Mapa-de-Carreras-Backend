from rest_framework import serializers
from ..validators import validar_nueva_contraseña

class CambiarContrasenaSerializer(serializers.Serializer):
    """
    Serializer para que un usuario (logueado) cambie su contraseña.
    """
    old_password = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        # 1. Lógica ÚNICA de este serializer
        user = self.context['request'].user
        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({"old_password": "La contraseña actual es incorrecta."})
        # --- 2. USA LA LÓGICA CENTRALIZADA ---
        validar_nueva_contraseña(data['password'], data['password2'])
        return data

    def update(self, instance, validated_data):
        # Guardamos la nueva contraseña
        instance.set_password(validated_data['password'])
        instance.save()
        return instance