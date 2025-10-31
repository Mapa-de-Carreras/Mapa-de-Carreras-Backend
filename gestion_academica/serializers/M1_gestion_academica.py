# gestion_academica/serializers/M1_gestion_academica.py

from rest_framework import serializers
from gestion_academica import models


class InstitutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Instituto
        fields = ['id', 'codigo', 'nombre', 'activo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at','activo']
        
    def validate(self, data):
        if 'activo' not in data:
            data['activo'] = True
        return data

    def validate_codigo(self, value):
        if models.Instituto.objects.filter(codigo=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ya existe un instituto con este código.")
        return value

    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del instituto no puede estar vacío.")
        return value


class CarreraSerializer(serializers.ModelSerializer):
    
    instituto = InstitutoSerializer(read_only=True)
   
    class Meta:
        model = models.Carrera
        fields = [
            "id", "codigo", "nombre", "nivel", "esta_vigente",
            "instituto", "instituto_id", "created_at", "updated_at"
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



class CarreraCreateUpdateSerializer(serializers.ModelSerializer):
    instituto_id = serializers.PrimaryKeyRelatedField(
        source="instituto",
        queryset=models.Instituto.objects.all(),
        write_only=True
    )

    class Meta:
        model = models.Carrera
        fields = ["codigo", "nombre", "nivel", "esta_vigente", "instituto_id"]
        read_only_fields = ['id', 'created_at', 'updated_at',"esta_vigente"]
    
    def validate(self, data):
        if 'esta_vigente' not in data:
            data['esta_vigente'] = True
        return data
    
    def validate_codigo(self, value):
        if models.Carrera.objects.filter(codigo=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ya existe una carrera con este código.")
        return value
    
    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre de la carrera no puede estar vacío.")
        return value
    

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