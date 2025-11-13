
from rest_framework import serializers
from gestion_academica.models import Instituto,Asignatura,PlanAsignatura,Correlativa


class InstitutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instituto
        fields = ['id', 'codigo', 'nombre', 'activo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at','activo']
        
    def validate(self, data):
        if 'activo' not in data:
            data['activo'] = True
        return data

    def validate_codigo(self, value):
        if Instituto.objects.filter(codigo=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ya existe un instituto con este código.")
        return value

    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del instituto no puede estar vacío.")
        return value

class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignatura
        fields = [
            "id", "codigo", "nombre", "activo", "cuatrimestre",
            "tipo_asignatura", "tipo_duracion",
            "horas_teoria", "horas_practica",
            "horas_semanales", "horas_totales",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "horas_totales","activo"]

    def validate(self, data):
        """Validaciones de consistencia."""
        if data.get("horas_teoria", 0) < 0 or data.get("horas_practica", 0) < 0:
            raise serializers.ValidationError("Las horas de teoría o práctica no pueden ser negativas.")

        total = data.get("horas_teoria", 0) + data.get("horas_practica", 0)
        if "horas_totales" in data and data["horas_totales"] != total:
            raise serializers.ValidationError("Las horas totales deben ser la suma de teoría + práctica.")

        return data

    def create(self, validated_data):
        """Calcula las horas totales al crear."""
        validated_data["horas_totales"] = (
            validated_data.get("horas_teoria", 0) +
            validated_data.get("horas_practica", 0)
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Recalcula las horas totales al actualizar."""
        validated_data["horas_totales"] = (
            validated_data.get("horas_teoria", instance.horas_teoria) +
            validated_data.get("horas_practica", instance.horas_practica)
        )
        return super().update(instance, validated_data)


class CorrelativaSerializer(serializers.ModelSerializer):
    plan_asignatura = serializers.PrimaryKeyRelatedField(
        queryset=PlanAsignatura.objects.all(),
    )
    correlativa_requerida = serializers.PrimaryKeyRelatedField(
        queryset=PlanAsignatura.objects.all(),
    )

    class Meta:
        model = Correlativa
        fields = ["id", "plan_asignatura", "correlativa_requerida"]