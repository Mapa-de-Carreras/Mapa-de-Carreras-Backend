import re
from rest_framework import serializers

def validar_nueva_contraseña(password, password2):
    """
    Función centralizada para validar la complejidad
    y la coincidencia de una nueva contraseña.
    """
    
    # 1. Validación de coincidencia
    if password != password2:
        raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

    # 2. Validación de complejidad
    if len(password) < 8:
        raise serializers.ValidationError({"password": "La contraseña debe tener al menos 8 caracteres."})
    if not re.search(r'[A-Z]', password):
        raise serializers.ValidationError({"password": "La contraseña debe contener al menos una letra mayúscula."})
    if not re.search(r'[0-9]', password):
        raise serializers.ValidationError({"password": "La contraseña debe contener al menos un número."})
    
    # Si todo está bien, no devuelve nada