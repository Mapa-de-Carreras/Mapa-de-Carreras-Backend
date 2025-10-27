# gestion_academica/serializers/auth_serializers/validar_email_serializer.py

# En alguno de tus archivos de serializers
from rest_framework import serializers


class EmailSerializer(serializers.Serializer):
    """Un serializer simple que solo valida un email."""
    email = serializers.EmailField()
