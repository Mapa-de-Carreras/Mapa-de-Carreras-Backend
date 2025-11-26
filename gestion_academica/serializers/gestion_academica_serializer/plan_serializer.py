
from rest_framework import serializers
from gestion_academica.models import PlanDeEstudio,PlanAsignatura,Carrera,Documento,Asignatura,Correlativa
from .asignatura_serializer import AsignaturaConCorrelativasSerializer,AsignaturaSerializer
from .carrera_serializer import CarreraSerializerDetail
from .documento_serializer import DocumentoSerializer



class CorrelativaSerializer(serializers.ModelSerializer):
    asignatura_origen = serializers.CharField(source="plan_asignatura.asignatura.nombre", read_only=True)
    asignatura_requerida = serializers.CharField(source="correlativa_requerida.asignatura.nombre", read_only=True)
    anio_asignatura = serializers.IntegerField(source="plan_asignatura.anio", read_only=True)
    anio_requerida = serializers.IntegerField(source="correlativa_requerida.anio", read_only=True)

    class Meta:
        model = Correlativa
        fields = [
            "id",
            "plan_asignatura",
            "correlativa_requerida",
            "asignatura_origen",
            "asignatura_requerida",
            "anio_asignatura",
            "anio_requerida",
        ]
    
class CorrelativaCreateSerializer(serializers.ModelSerializer):
    plan_asignatura_id = serializers.PrimaryKeyRelatedField(
        source="plan_asignatura",
        queryset=PlanAsignatura.objects.all(),
        write_only=True
    )
    correlativa_requerida_id = serializers.PrimaryKeyRelatedField(
        source="correlativa_requerida",
        queryset=PlanAsignatura.objects.all(),
        write_only=True
    )

    class Meta:
        model = Correlativa
        fields = ["plan_asignatura_id", "correlativa_requerida_id"]

    def validate(self, data):
        plan_asignatura = data["plan_asignatura"]
        correlativa_requerida = data["correlativa_requerida"]

        # Regla 1: misma plan de estudio
        if plan_asignatura.plan_de_estudio_id != correlativa_requerida.plan_de_estudio_id:
            raise serializers.ValidationError(
                "Las correlativas deben pertenecer al mismo plan de estudio."
            )

        # Regla 2: no puede ser correlativa de sí misma
        if plan_asignatura == correlativa_requerida:
            raise serializers.ValidationError(
                "Una asignatura no puede ser correlativa de sí misma."
            )

        # Regla 3: no puede ser correlativa de una del mismo año y cuatrimestre
        if (plan_asignatura.anio == correlativa_requerida.anio and
            plan_asignatura.asignatura.cuatrimestre == correlativa_requerida.asignatura.cuatrimestre):
            raise serializers.ValidationError(
                "No se pueden establecer correlativas entre asignaturas del mismo año y cuatrimestre."
            )

        return data
    

class PlanDeEstudioSerializerList(serializers.ModelSerializer):
    creado_por = serializers.SerializerMethodField()    
    documento = DocumentoSerializer(read_only=True)
    carrera_nombre=serializers.CharField(source="carrera.nombre",read_only=True)
    carrera_id=serializers.IntegerField(source="carrera.id",read_only=True)
    class Meta:
        model = PlanDeEstudio
        fields = [
            "id", "fecha_inicio", "esta_vigente","creado_por","created_at", "updated_at","documento","carrera_nombre","carrera_id"
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
    documento = DocumentoSerializer(read_only=True)
    asignaturas = serializers.SerializerMethodField()
    creado_por = serializers.SerializerMethodField()
    carrera=CarreraSerializerDetail(read_only=True)
    class Meta:
        model = PlanDeEstudio
        fields = [
            "id",
            "fecha_inicio",
            "esta_vigente",
            "creado_por",
            "documento",
            "asignaturas",
            "created_at",
            "updated_at",
            "documento",
            "carrera",
        ]

    def get_asignaturas(self, obj):
        asignaturas = (
            obj.asignaturas.all()
            .select_related()
            .order_by("cuatrimestre", "codigo")
        )

        # pasamos el plan al serializer para obtener correlativas
        return AsignaturaConCorrelativasSerializer(
            asignaturas,
            many=True,
            context={"plan": obj}
        ).data

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
    
    documento_id = serializers.PrimaryKeyRelatedField(
        source="documento", queryset=Documento.objects.all(),
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = PlanDeEstudio
        fields = ["fecha_inicio", "esta_vigente", "carrera_id", "documento_id"]

    def validate(self, data):
        carrera = data.get("carrera") or getattr(self.instance, "carrera", None)
        documento = data.get("documento") or getattr(self.instance, "documento", None)

        if carrera and documento:
            existe = PlanDeEstudio.objects.filter(
                carrera=carrera,
                documento=documento
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
        
        

class PlanAsignaturaSerializer(serializers.ModelSerializer):
    plan_de_estudio_id = serializers.PrimaryKeyRelatedField(
        source="plan_de_estudio",
        queryset=PlanDeEstudio.objects.all()
    )
    asignatura_id = serializers.PrimaryKeyRelatedField(
        source="asignatura",
        queryset=Asignatura.objects.all()
    )
    asignatura_nombre = serializers.CharField(
        source="asignatura.nombre",
        read_only=True
    )
    descripcion = serializers.SerializerMethodField()

    class Meta:
        model = PlanAsignatura
        fields = [
            "id",
            "plan_de_estudio_id",
            "asignatura_id",
            "asignatura_nombre",
            "anio",
            "horas_teoria",
            "horas_practica",
            "horas_semanales",
            "horas_totales",
            "created_at",
            "updated_at",
            "descripcion"
        ]
        read_only_fields = ["id", "horas_totales", "created_at", "updated_at"]

    def get_descripcion(self, obj):
        return str(obj)

    def validate(self, data):
        plan = data.get("plan_de_estudio")
        asignatura = data.get("asignatura")

        # Asignaturas inactivas no se pueden agregar
        if not asignatura.activo:
            raise serializers.ValidationError(
                "No se puede asociar una asignatura inactiva al plan de estudio."
            )

        # Evitar la validación cuando estamos editando el mismo objeto
        instancia = getattr(self, "instance", None)

        if instancia:
            # Si el plan o la asignatura cambian, recién ahí validar duplicado
            plan_cambia = plan != instancia.plan_de_estudio
            asignatura_cambia = asignatura != instancia.asignatura

            if plan_cambia or asignatura_cambia:
                if PlanAsignatura.objects.filter(
                    plan_de_estudio=plan, asignatura=asignatura
                ).exists():
                    raise serializers.ValidationError(
                        "Esta asignatura ya está asociada a este plan."
                    )
        else:
            # Si es un create (POST), validar normal
            if PlanAsignatura.objects.filter(
                plan_de_estudio=plan, asignatura=asignatura
            ).exists():
                raise serializers.ValidationError(
                    "Esta asignatura ya está asociada a este plan."
                )

        return data


        

