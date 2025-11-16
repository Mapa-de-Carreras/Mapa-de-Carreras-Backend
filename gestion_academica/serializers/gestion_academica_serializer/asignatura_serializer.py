
from rest_framework import serializers
from gestion_academica.models import Instituto,Asignatura,PlanAsignatura,Correlativa


class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignatura
        fields = [
            "id", "codigo", "nombre", "activo", "cuatrimestre",
            "tipo_asignatura", "tipo_duracion",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at","activo"]