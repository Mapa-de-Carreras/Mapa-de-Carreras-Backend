
from rest_framework import serializers
from gestion_academica.models import Carrera,Instituto,CarreraCoordinacion
from .instituto_serializer  import InstitutoSerializer


class CarreraSerializerList(serializers.ModelSerializer):
    instituto = InstitutoSerializer(read_only=True)
   
    class Meta:
        model = Carrera
        fields = [
            "id", "codigo", "nombre", "nivel", "esta_vigente", "created_at", "updated_at",'instituto'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
class CarreraSerializerDetail(serializers.ModelSerializer):
    instituto = InstitutoSerializer(read_only=True)
    planes = serializers.SerializerMethodField()
    coordinador_actual = serializers.SerializerMethodField()

    class Meta:
        model = Carrera
        fields = [
            "id",
            "codigo",
            "nombre",
            "nivel",
            "esta_vigente",
            "coordinador_actual",
            "instituto",
            "planes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_planes(self, obj):
        # Import local para evitar el import circular
        from .plan_serializer import PlanDeEstudioSerializerList
        planes = obj.planes.all()  # usa el related_name definido en el modelo
        return PlanDeEstudioSerializerList(planes, many=True).data

    def get_coordinador_actual(self, obj):
        """Devuelve el coordinador activo actual de la carrera."""
        try:
            # Buscamos el registro de coordinación más reciente y activo
            coordinacion = (
                CarreraCoordinacion.objects
                .filter(carrera=obj, activo=True)
                .order_by("-fecha_inicio", "-created_at")
                .select_related("coordinador")
                .first()
            )

            if coordinacion and coordinacion.coordinador:
                coord = coordinacion.coordinador
                return {
                    "id": coord.id,
                    "username": coord.username,
                    "nombre_completo": f"{coord.first_name} {coord.last_name}".strip(),
                    "email": coord.email,
                    "fecha_inicio": coordinacion.fecha_inicio,
                }
        except Exception as e:
            # (opcional: útil en debug)
            print(f"Error al obtener coordinador actual: {e}")

        return None

class CarreraVigenciaUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Carrera
        fields = ["esta_vigente"]
        

class CarreraCreateUpdateSerializer(serializers.ModelSerializer):
    instituto_id = serializers.PrimaryKeyRelatedField(
        source="instituto",
        queryset=Instituto.objects.filter(activo=True),
        write_only=True,
        error_messages={
            "does_not_exist": "El instituto seleccionado no existe o no está activo.",
            "incorrect_type": "El valor de instituto_id debe ser un número entero válido."
        }
    )

    class Meta:
        model = Carrera
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
        qs = Carrera.objects.filter(codigo__iexact=value)
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
        qs = Carrera.objects.filter(nombre__iexact=nombre_normalizado)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError("Ya existe una carrera con este nombre (no se distingue mayúsculas o espacios).")
        return value