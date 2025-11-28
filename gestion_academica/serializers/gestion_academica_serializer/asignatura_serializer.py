
from rest_framework import serializers
from gestion_academica.models import Instituto,Asignatura,PlanAsignatura,Correlativa


class AsignaturaSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Asignatura
        fields = [
            "id", "codigo", "nombre", "activo", "cuatrimestre",
            "tipo_asignatura", "tipo_duracion",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "activo"]

class AsignaturaDetailSerializer(AsignaturaSerializer):
    # Asumo que ya creaste el PlanAsignaturaDetalleSerializer en el paso anterior
    planes_asignatura = serializers.SerializerMethodField()

    class Meta(AsignaturaSerializer.Meta):
        # Extendemos los campos del padre agregando el nuevo
        fields = AsignaturaSerializer.Meta.fields + ["planes_asignatura"]
    
    def get_planes_asignatura(self, obj):
        # Hacemos el import AQUÍ ADENTRO para evitar errores circulares
        from gestion_academica.serializers.gestion_academica_serializer.plan_serializer import PlanAsignaturaDetalleSerializer
        
        # Obtenemos la relación inversa
        qs = obj.planasignatura_set.all().select_related('plan_de_estudio__carrera')
        
        # Retornamos la data serializada
        return PlanAsignaturaDetalleSerializer(qs, many=True).data


class AsignaturaConCorrelativasSerializer(serializers.ModelSerializer):
    correlativas = serializers.SerializerMethodField()

    class Meta:
        model = Asignatura
        fields = [
            "id", "codigo", "nombre", "activo", "cuatrimestre",
            "tipo_asignatura", "tipo_duracion",
            "created_at", "updated_at",
            "correlativas"
        ]

    def get_correlativas(self, asignatura):
        """Busca correlativas usando PlanAsignatura → Correlativa."""
        plan = self.context.get("plan")  # lo pasamos desde el serializer padre
        if not plan:
            return []

        # buscamos el PlanAsignatura correspondiente
        try:
            pa = PlanAsignatura.objects.get(
                plan_de_estudio=plan, asignatura=asignatura
            )
        except PlanAsignatura.DoesNotExist:
            return []

        # obtenemos correlativas reales (asignaturas)
        correlativas = pa.correlativas_requeridas.select_related(
            "correlativa_requerida__asignatura"
        )

        return [
            AsignaturaSerializer(c.correlativa_requerida.asignatura).data
            for c in correlativas
        ]

class CorrelativaSerializer(serializers.ModelSerializer):
    plan_asignatura = serializers.PrimaryKeyRelatedField(
        queryset=PlanAsignatura.objects.all(),
    )
    correlativa_requerida = serializers.PrimaryKeyRelatedField(
        queryset=PlanAsignatura.objects.all(),
    )

    class Meta:
        model = Correlativa
        fields = ["id", "plan_asignatura", "correlativa_requerida"]