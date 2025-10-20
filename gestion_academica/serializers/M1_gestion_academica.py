# gestion_academica/serializers/M1_gestion_academica.py

from rest_framework import serializers
from gestion_academica import models


class InstitutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Instituto
        fields = ['id', 'codigo', 'nombre',
                  'activo', 'created_at', 'updated_at']


class CarreraSerializer(serializers.ModelSerializer):
    # muestra los datos completos del instituto (solo lectura)
    instituto = InstitutoSerializer(read_only=True)
    # permite asociar una carrera usando el id del instituto
    instituto_id = serializers.PrimaryKeyRelatedField(
        source="instituto",
        queryset=models.Instituto.objects.all(),
        write_only=True
    )

    class Meta:
        model = models.Carrera
        fields = [
            "id", "codigo", "nombre", "nivel", "esta_vigente",
            "instituto", "instituto_id", "created_at", "updated_at"
        ]


class ResolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Resolucion
        fields = [
            "id", "tipo", "emisor", "numero", "anio", "created_at", "updated_at"
        ]


class AsignaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Asignatura
        fields = [
            "id", "codigo", "nombre", "activo",
            "cuatrimestre", "tipo_asignatura", "tipo_duracion",
            "horas_teoria", "horas_practica", "horas_semanales",
            "horas_totales", "created_at", "updated_at"
        ]
        # solo lectura porque el modelo lo calcula automaticamente
        read_only_fields = ["horas_totales"]


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Documento
        fields = [
            "id", "tipo", "emisor", "numero",
            "anio", "archivo", "created_at"
        ]


class PlanAsignaturaSerializer(serializers.ModelSerializer):
    asignatura = AsignaturaSerializer(read_only=True)
    asignatura_id = serializers.PrimaryKeyRelatedField(
        source="asignatura",
        queryset=models.Asignatura.objects.all(),
        write_only=True
    )

    class Meta:
        model = models.PlanAsignatura
        fields = [
            "id", "plan_de_estudio", "asignatura", "asignatura_id",
            "anio", "created_at", "updated_at"
        ]


class PlanDeEstudioSerializer(serializers.ModelSerializer):
    # referencias a Resolucion, Carrera y Documento
    resolucion = ResolucionSerializer(read_only=True)
    resolucion_id = serializers.PrimaryKeyRelatedField(
        source="resolucion",
        queryset=models.Resolucion.objects.all(),
        write_only=True
    )

    carrera = CarreraSerializer(read_only=True)
    carrera_id = serializers.PrimaryKeyRelatedField(
        source="carrera",
        queryset=models.Carrera.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    documento = DocumentoSerializer(read_only=True)
    documento_id = serializers.PrimaryKeyRelatedField(
        source="documento",
        queryset=models.Documento.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    # mostramos las asignaturas del plan a través del through (PlanAsignatura)
    asignaturas = PlanAsignaturaSerializer(
        source="planasignatura_set", many=True, read_only=True
    )

    class Meta:
        model = models.PlanDeEstudio
        fields = [
            "id", "fecha_inicio", "esta_vigente",
            "documento", "documento_id",
            "resolucion", "resolucion_id",
            "carrera", "carrera_id",
            "asignaturas", "creado_por",
            "created_at", "updated_at"
        ]
        read_only_fields = ["asignaturas"]


class CorrelativaSerializer(serializers.ModelSerializer):
    plan_asignatura = serializers.PrimaryKeyRelatedField(
        queryset=models.PlanAsignatura.objects.all(),
    )
    correlativa_requerida = serializers.PrimaryKeyRelatedField(
        queryset=models.PlanAsignatura.objects.all(),
    )

    class Meta:
        model = models.Correlativa
        fields = ["id", "plan_asignatura", "correlativa_requerida"]
