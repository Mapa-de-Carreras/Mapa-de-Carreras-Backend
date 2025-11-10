# gestion_academica/serializers/M3_designaciones_docentes.py

from django.contrib.auth import get_user_model
from rest_framework import serializers
from gestion_academica import models
from gestion_academica_serializer import AsignaturaSerializer
from gestion_academica.serializers.M2_gestion_docentes import DocenteSerializer, ParametrosRegimenSerializer


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
    docente_id = serializers.PrimaryKeyRelatedField(
        source="docente",
        queryset=models.Docente.objects.all(),
        write_only=True,
        required=True
    )

    comision_id = serializers.PrimaryKeyRelatedField(
        source="comision",
        queryset=models.Comision.objects.all(),
        write_only=True,
        required=True
    )

    cargo_id = serializers.PrimaryKeyRelatedField(
        source="cargo",
        queryset=models.Cargo.objects.all(),
        write_only=True,
        required=True
    )

    documento_id = serializers.PrimaryKeyRelatedField(
        source="documento",
        queryset=models.Documento.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    creado_por = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    dedicacion_id = serializers.PrimaryKeyRelatedField(
        source="dedicacion",
        write_only=True,
        queryset=models.Dedicacion.objects.all(),
        required=True
    )

    modalidad_id = serializers.PrimaryKeyRelatedField(
        source="modalidad",
        write_only=True,
        queryset=models.Modalidad.objects.all(),
        required=False,
        allow_null=True
    )

    regimen_id = serializers.PrimaryKeyRelatedField(
        source="regimen",
        write_only=True,
        queryset=models.ParametrosRegimen.objects.all(),
        required=False,
        allow_null=True
    )

    docente = DocenteSerializer(read_only=True)
    comision = ComisionSerializer(read_only=True)
    regimen = ParametrosRegimenSerializer(read_only=True)
    cargo = CargoSerializer(read_only=True)

    class Meta:
        model = models.Designacion
        fields = [
            "id", "fecha_inicio", "fecha_fin", "tipo_designacion",
            "docente", "docente_id", "comision", "comision_id",
            "regimen", "regimen_id", "cargo", "cargo_id", "observacion", "documento", "documento_id",
            "dedicacion_id", "modalidad_id", "creado_por", "created_at",
            "updated_at"
        ]
        read_only_fields = ["creado_por",
                            "created_at", "updated_at", "regimen"]

    def validate(self, data):
        inicio = data.get("fecha_inicio")
        fin = data.get("fecha_fin")
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                {"fecha_fin": "La fecha de fin no puede ser anterior a la fecha de inicio."})

        # si cargo es Contratado -> no debe tener documento/resolución asociada
        cargo = data.get("cargo")
        documento = data.get("documento")
        if cargo and cargo.nombre.lower() == "contratado" and documento is not None:
            raise serializers.ValidationError(
                {"documento": "Las designaciones 'Contratado' no deben venir con documento/resolución asociada."})

        return data
