from rest_framework import serializers
from gestion_academica import models
from gestion_academica.serializers.user_serializers.role_serializer import RoleSerializer


class LeerUsuarioSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    docente_data = serializers.SerializerMethodField()
    coordinador_data = serializers.SerializerMethodField()

    class Meta:
        model = models.Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_active', 'legajo', 'fecha_nacimiento', 'celular',
            'roles', 'docente_data', 'coordinador_data'
        ]
        read_only_fields = fields

    def get_docente_data(self, obj):
        if hasattr(obj, 'docente') and obj.docente is not None:
            from gestion_academica.serializers.M2_gestion_docentes import DocenteSerializer
            return DocenteSerializer(obj.docente).data
        return None

    def get_coordinador_data(self, obj):
        if hasattr(obj, 'coordinador') and obj.coordinador is not None:
            from gestion_academica.serializers.user_serializers.usuario_serializer import CoordinadorSerializer
            return CoordinadorSerializer(obj.coordinador).data
        return None
