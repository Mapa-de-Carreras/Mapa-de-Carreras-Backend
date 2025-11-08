# gestion_academica/serializers/M3_designaciones_docentes.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from gestion_academica import models



User = get_user_model()


class ComisionSerializer(serializers.ModelSerializer):
    asignatura_nombre = serializers.CharField(source="asignatura.nombre", read_only=True)

    class Meta:
        model = models.Comision
        fields = [
            "id", "nombre", "turno", "promocionable", "activo",
            "asignatura", "asignatura_nombre"
        ]
        read_only_fields = ["id", "asignatura_nombre"]


class ComisionCreateUpdateSerializer(serializers.ModelSerializer):
    asignatura_id = serializers.PrimaryKeyRelatedField(
        source="asignatura", queryset=models.Asignatura.objects.all(), write_only=True
    )

    class Meta:
        model = models.Comision
        fields = ["nombre", "turno", "promocionable", "activo", "asignatura_id"]

    def validate(self, data):
        asignatura = data.get("asignatura") or getattr(self.instance, "asignatura", None)
        nombre = data.get("nombre") or getattr(self.instance, "nombre", None)

        if models.Comision.objects.filter(
            asignatura=asignatura, nombre__iexact=nombre
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                f"Ya existe una comisión llamada '{nombre}' para esta asignatura."
            )
        return data


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cargo
        fields = ["id", "nombre", "created_at", "updated_at"]


class DesignacionSerializer(serializers.ModelSerializer):
    docente = serializers.PrimaryKeyRelatedField(
        queryset=models.Docente.objects.all()
    )

    comision = serializers.PrimaryKeyRelatedField(
        queryset=models.Comision.objects.all()
    )

    regimen = serializers.PrimaryKeyRelatedField(
        queryset=models.ParametrosRegimen.objects.all()
    )

    cargo = serializers.PrimaryKeyRelatedField(
        queryset=models.Cargo.objects.all()
    )

    creado_por = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = models.Designacion
        fields = [
            "id", "fecha_inicio", "fecha_fin", "tipo_designacion",
            "docente", "comision", "regimen", "cargo",
            "observacion", "documento", "creado_por", "created_at", "updated_at"
        ]