# gestion_academica/serializers/M3_designaciones_docentes.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from gestion_academica import models
from gestion_academica.serializers.M1_gestion_academica import AsignaturaSerializer


User = get_user_model()


class ComisionSerializer(serializers.ModelSerializer):
    asignatura = AsignaturaSerializer(read_only=True)
    # asignatura = serializers.PrimaryKeyRelatedField(read_only=True)
    asignatura_id = serializers.PrimaryKeyRelatedField(
        source="asignatura",
        write_only=True,
        queryset=models.Asignatura.objects.all()
    )

    class Meta:
        model = models.Comision
        fields = [
            "id", "nombre", "turno", "promocionable",
            "activo", "asignatura", "asignatura_id"
        ]


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
