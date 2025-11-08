
from rest_framework import serializers
from gestion_academica.models import PlanDeEstudio,Resolucion,PlanAsignatura,Carrera,Documento,Asignatura
from .asignatura_serializer import AsignaturaSerializer


class PlanAsignaturaSerializer(serializers.ModelSerializer):
    asignatura = AsignaturaSerializer(read_only=True)
    asignatura_id = serializers.PrimaryKeyRelatedField(
        source="asignatura",
        queryset=Asignatura.objects.all(),
        write_only=True
    )

    class Meta:
        model = PlanAsignatura
        fields = [
            "id", "plan_de_estudio", "asignatura", "asignatura_id",
            "anio", "created_at", "updated_at"
        ]


class PlanDeEstudioSerializerList(serializers.ModelSerializer):
    creado_por = serializers.SerializerMethodField()        

    class Meta:
        model = PlanDeEstudio
        fields = [
            "id", "fecha_inicio", "esta_vigente","creado_por","created_at", "updated_at"
        ]
        
    def get_creado_por(self, obj):
        if obj.creado_por:
            return {
                "id": obj.creado_por.id,
                "username": obj.creado_por.username,
                "nombre_completo": f"{obj.creado_por.first_name} {obj.creado_por.last_name}".strip(),
                "email": obj.creado_por.email,
            }
        return None

class PlanDeEstudioSerializerDetail(serializers.ModelSerializer):
    documento = serializers.StringRelatedField(read_only=True)
    asignaturas = AsignaturaSerializer(read_only=True, many=True)
    creado_por = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanDeEstudio
        fields = [
            "id", "fecha_inicio", "esta_vigente","creado_por" ,"documento", "asignaturas",
            "created_at", "updated_at"
        ]
        
    def get_creado_por(self, obj):
        if obj.creado_por:
            return {
                "id": obj.creado_por.id,
                "username": obj.creado_por.username,
                "nombre_completo": f"{obj.creado_por.first_name} {obj.creado_por.last_name}".strip(),
                "email": obj.creado_por.email,
            }
        return None


class PlanDeEstudioCreateUpdateSerializer(serializers.ModelSerializer):
    carrera_id = serializers.PrimaryKeyRelatedField(
        source="carrera", queryset=Carrera.objects.all(), write_only=True
    )
    resolucion_id = serializers.PrimaryKeyRelatedField(
        source="resolucion", queryset=Resolucion.objects.all(), write_only=True
    )
    documento_id = serializers.PrimaryKeyRelatedField(
        source="documento", queryset=Documento.objects.all(),
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = PlanDeEstudio
        fields = ["fecha_inicio", "esta_vigente", "carrera_id", "resolucion_id", "documento_id"]

    def validate(self, data):
        carrera = data.get("carrera") or getattr(self.instance, "carrera", None)
        resolucion = data.get("resolucion") or getattr(self.instance, "resolucion", None)

        if carrera and resolucion:
            existe = PlanDeEstudio.objects.filter(
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
        model = PlanDeEstudio
        fields = ["esta_vigente"]
        
        
class ResolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resolucion
        fields = [
            "id", "tipo", "emisor", "numero", "anio", "created_at", "updated_at"
        ]
        

class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = [
            "id", "tipo", "emisor", "numero",
            "anio", "archivo", "created_at"
        ]