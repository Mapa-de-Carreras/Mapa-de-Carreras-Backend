
from rest_framework import serializers
from gestion_academica.models import Carrera,Instituto,CarreraCoordinacion
from .instituto_serializer  import InstitutoSerializer


class CarreraSerializerList(serializers.ModelSerializer):
    instituto = InstitutoSerializer(read_only=True)
    coordinador_actual = serializers.SerializerMethodField()
   
    class Meta:
        model = Carrera
        fields = [
            "id", "codigo", "nombre", "nivel", "esta_vigente", "created_at", "updated_at",'instituto',"coordinador_actual"
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def get_coordinador_actual(self, obj):
            coordinacion = (
                CarreraCoordinacion.objects
                .filter(carrera=obj, activo=True)
                .select_related("coordinador__usuario")
                .order_by("-fecha_inicio", "-created_at")
                .first()
            )

            if not coordinacion or not coordinacion.coordinador:
                return None

            usuario = coordinacion.coordinador.usuario

            return {
                "id": usuario.id,
                "username": usuario.username,
                "nombre_completo": f"{usuario.first_name} {usuario.last_name}".strip(),
                "email": usuario.email,
                "fecha_inicio": coordinacion.fecha_inicio,
            }
        
class CarreraSerializerDetail(serializers.ModelSerializer):
    instituto = InstitutoSerializer(read_only=True)
    planes = serializers.SerializerMethodField()
    coordinador_actual = serializers.SerializerMethodField()
    coordinadores_historial = serializers.SerializerMethodField()

    class Meta:
        model = Carrera
        fields = [
            "id",
            "codigo",
            "nombre",
            "nivel",
            "esta_vigente",
            "coordinador_actual",
            "coordinadores_historial",
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
            coordinacion = (
                CarreraCoordinacion.objects
                .filter(carrera=obj, activo=True)
                .select_related("coordinador__usuario")
                .order_by("-fecha_inicio", "-created_at")
                .first()
            )

            if not coordinacion or not coordinacion.coordinador:
                return None

            usuario = coordinacion.coordinador.usuario

            return {
                "id": usuario.id,
                "username": usuario.username,
                "nombre_completo": f"{usuario.first_name} {usuario.last_name}".strip(),
                "email": usuario.email,
                "fecha_inicio": coordinacion.fecha_inicio,
            }

        # --------------------------
        #  🔹 Historial coordinadores
        # --------------------------
    def get_coordinadores_historial(self, obj):
            """
            Devuelve todos los coordinadores (actuales e históricos) 
            con sus fechas de inicio/fin y estado.
            """
            coordinaciones = (
                CarreraCoordinacion.objects
                .filter(carrera=obj)
                .select_related("coordinador__usuario")
                .order_by("-fecha_inicio")
            )

            historial = []
            for c in coordinaciones:
                usuario = c.coordinador.usuario
                historial.append({
                    "id": usuario.id,
                    "username": usuario.username,
                    "nombre_completo": f"{usuario.first_name} {usuario.last_name}".strip(),
                    "email": usuario.email,
                    "fecha_inicio": c.fecha_inicio,
                    "fecha_fin": c.fecha_fin,
                    "activo": c.activo,
                })

            return historial
        
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