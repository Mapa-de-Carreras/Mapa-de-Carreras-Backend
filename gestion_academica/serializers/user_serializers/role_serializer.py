from rest_framework import serializers
from gestion_academica import models


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rol
        fields = ["id", "nombre", "descripcion"]
        read_only_fields = fields
