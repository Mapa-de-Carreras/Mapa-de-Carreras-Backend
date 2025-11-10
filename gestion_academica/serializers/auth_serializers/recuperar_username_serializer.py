# gestion_academica/serializers/auth_serializers/recuperar_username_serializer.py

from rest_framework import serializers
from gestion_academica import models


class RecuperarUsuarioSerializer(serializers.Serializer):
    """ Valida que el email exista en la BD para recuperar el username. """
    email = serializers.EmailField()

    def validate(self, data):
        email = data.get('email')
        try:
            user = models.Usuario.objects.get(email=email)
            data['user'] = user
        except models.Usuario.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "No existe una cuenta asociada a este correo electrónico."})
        return data
