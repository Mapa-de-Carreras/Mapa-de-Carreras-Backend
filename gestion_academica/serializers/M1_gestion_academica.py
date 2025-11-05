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

class CarreraVigenciaUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = models.Carrera
        fields = ["esta_vigente"]
        

class CarreraCreateUpdateSerializer(serializers.ModelSerializer):
    instituto_id = serializers.PrimaryKeyRelatedField(
        source="instituto",
        queryset=models.Instituto.objects.filter(activo=True),
        write_only=True,
        error_messages={
            "does_not_exist": "El instituto seleccionado no existe o no está activo.",
            "incorrect_type": "El valor de instituto_id debe ser un número entero válido."
        }
    )

    class Meta:
        model = models.Carrera
        fields = ["codigo", "nombre", "nivel", "instituto_id"]
        read_only_fields = ["esta_vigente"]

    # -------------------------------
    # Validaciones generales
    # -------------------------------
    def validate(self, data):
        # Si no se indica, se asume que la carrera es vigente
        if "esta_vigente" not in data:
            data["esta_vigente"] = True
        return data

    # -------------------------------
    # Validación: código único (no sensible a mayúsculas)
    # -------------------------------
    def validate_codigo(self, value):
        value = value.strip().upper()
        qs = models.Carrera.objects.filter(codigo__iexact=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una carrera con este código (no se distingue mayúsculas).")
        return value

    # -------------------------------
    # Validación: nombre único (no sensible a mayúsculas ni espacios)
    # -------------------------------
    def validate_nombre(self, value):
        nombre_normalizado = " ".join(value.strip().split()).upper()  # elimina espacios dobles y pasa a mayúsculas
        qs = models.Carrera.objects.filter(nombre__iexact=nombre_normalizado)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una carrera con este nombre (no se distingue mayúsculas o espacios).")
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
    carrera = CarreraSerializer(read_only=True)
    resolucion = serializers.StringRelatedField(read_only=True)
    documento = serializers.StringRelatedField(read_only=True)
    asignaturas = AsignaturaSerializer(read_only=True, many=True)

    class Meta:
        model = models.PlanDeEstudio
        fields = [
            "id", "fecha_inicio", "esta_vigente", "carrera",
            "resolucion", "documento", "asignaturas",
            "created_at", "updated_at"
        ]


class PlanDeEstudioCreateUpdateSerializer(serializers.ModelSerializer):
    carrera_id = serializers.PrimaryKeyRelatedField(
        source="carrera", queryset=models.Carrera.objects.all(), write_only=True
    )
    resolucion_id = serializers.PrimaryKeyRelatedField(
        source="resolucion", queryset=models.Resolucion.objects.all(), write_only=True
    )
    documento_id = serializers.PrimaryKeyRelatedField(
        source="documento", queryset=models.Documento.objects.all(),
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = models.PlanDeEstudio
        fields = ["fecha_inicio", "esta_vigente", "carrera_id", "resolucion_id", "documento_id"]

    def validate(self, data):
        carrera = data.get("carrera") or getattr(self.instance, "carrera", None)
        resolucion = data.get("resolucion") or getattr(self.instance, "resolucion", None)

        if carrera and resolucion:
            existe = models.PlanDeEstudio.objects.filter(
                carrera=carrera,
                resolucion=resolucion
            ).exclude(id=self.instance.id if self.instance else None).exists()

            if existe:
                raise serializers.ValidationError(
                    "Ya existe un plan de estudios con esta resolución para la carrera."
                )

        return data
    

class PlanDeEstudioVigenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PlanDeEstudio
        fields = ["esta_vigente"]


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