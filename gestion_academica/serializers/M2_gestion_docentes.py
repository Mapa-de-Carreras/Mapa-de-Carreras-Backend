# gestion_academica/serializers/M2_gestion_docentes.py
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from gestion_academica import models
from gestion_academica.serializers.user_serializers.role_serializer import RoleSerializer


class CaracterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Caracter
        fields = ["id", "nombre", "created_at", "updated_at"]


class ModalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Modalidad
        fields = ["id", "nombre", "created_at", "updated_at"]


class DedicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Dedicacion
        fields = ["id", "nombre", "created_at", "updated_at"]


class ParametrosRegimenSerializer(serializers.ModelSerializer):
    modalidad = ModalidadSerializer(read_only=True)
    dedicacion = DedicacionSerializer(read_only=True)
    modalidad_id = serializers.PrimaryKeyRelatedField(
        source="modalidad",
        write_only=True,
        queryset=models.Modalidad.objects.all()
    )
    dedicacion_id = serializers.PrimaryKeyRelatedField(
        source="dedicacion",
        write_only=True,
        queryset=models.Dedicacion.objects.all()
    )

    class Meta:
        model = models.ParametrosRegimen
        fields = [
            "id", "modalidad", "dedicacion",
            "modalidad_id", "dedicacion_id",
            "horas_max_frente_alumnos", "horas_min_frente_alumnos",
            "horas_max_anual", "horas_min_anual", "activo",
            "max_asignaturas"
        ]


class UsuarioLiteSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = models.Usuario
        fields = [
            "id", "username", "first_name", "last_name",
            "email", "legajo", "celular", "roles"
        ]
        read_only_fields = fields


class DocenteSerializer(serializers.ModelSerializer):
    modalidad_id = serializers.PrimaryKeyRelatedField(
        source="modalidad",
        queryset=models.Modalidad.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    caracter_id = serializers.PrimaryKeyRelatedField(
        source="caracter",
        queryset=models.Caracter.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    dedicacion_id = serializers.PrimaryKeyRelatedField(
        source="dedicacion",
        queryset=models.Dedicacion.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    # usuario_id = serializers.IntegerField(source="usuario.id", read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        source="usuario",
        queryset=models.Usuario.objects.all(),
        write_only=True,
        required=False,
        allow_null=False
    )

    usuario = UsuarioLiteSerializer(read_only=True)
    activo = serializers.BooleanField()

    # representaciones en lectura (simple PKs)
    modalidad = ModalidadSerializer(read_only=True)
    caracter = CaracterSerializer(read_only=True)
    dedicacion = DedicacionSerializer(read_only=True)

    carreras = serializers.SerializerMethodField(read_only=True)

    cantidad_materias = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Docente
        # hereda todos los campos de Usuario mas los suyos
        fields = [
            "id",
            "usuario", "usuario_id",
            "modalidad", "modalidad_id",
            "caracter", "caracter_id",
            "dedicacion", "dedicacion_id",
            "cantidad_materias", "activo",
            "carreras"
        ]

        read_only_fields = ["modalidad",
                            "caracter", "dedicacion", "usuario", "carreras","cantidad_materias"]
    
    def get_cantidad_materias(self, obj):
        """
        Calcula la cantidad de materias (asignaturas distintas) del docente
        a partir de sus designaciones activas y vigentes.
        """
        from gestion_academica import models as ga

        hoy = timezone.now().date()

        qs = ga.Designacion.objects.filter(
            docente=obj,
            activo=True,
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=hoy)
        )

        return qs.values(
            "comision__plan_asignatura__asignatura"
        ).distinct().count()
    
    def get_carreras(self, obj):
        """
        Devuelve lista de carreras (id, nombre) relacionadas al docente
        por las designaciones -> comision -> asignatura -> planes_de_estudio -> carrera.
        """
        from django.db.models import Q
        from django.utils import timezone
        hoy = timezone.now()
        # obtenemos PlanDeEstudio relacionados con asignaturas que tienen comisiones con designaciones del docente
        planes_qs = models.PlanDeEstudio.objects.filter(
            # La ruta corregida:
            Q(planasignatura__comisiones__designaciones__fecha_fin__isnull=True) |
            Q(planasignatura__comisiones__designaciones__fecha_fin__gt=hoy),
            planasignatura__comisiones__designaciones__docente=obj,
            
            # Solo de planes vigentes
            esta_vigente=True,
            
            # Solo de designaciones activAS
            planasignatura__comisiones__designaciones__activo=True,            
            
        ).distinct().select_related('carrera')

        # convertir a lista de dicts con id/nombre de carrera (distinct)
        carreras = []
        seen = set()
        for plan in planes_qs:
            c = plan.carrera
            if c and c.id not in seen:
                seen.add(c.id)
                carreras.append({"id": c.id, "nombre": c.nombre})
        return carreras

    def update(self, instance, validated_data):
        '''Actualiza solo los campos permitidos'''
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DocenteDetalleSerializer(serializers.ModelSerializer):

    usuario = UsuarioLiteSerializer(read_only=True)

    modalidad = serializers.StringRelatedField(read_only=True)
    dedicacion = serializers.StringRelatedField(read_only=True)
    caracter = serializers.StringRelatedField(read_only=True)

    # Se traen las designaciones relacionadas
    designaciones = serializers.SerializerMethodField()
    carreras = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Docente
        fields = [
            "id", "usuario", "modalidad", "dedicacion", "caracter", "cantidad_materias",
            "designaciones", "carreras"
        ]
    
    def get_cantidad_materias(self, obj):
        from gestion_academica import models as ga

        hoy = timezone.now().date()

        qs = ga.Designacion.objects.filter(
            docente=obj,
            activo=True,
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=hoy)
        )

        return qs.values(
            "comision__plan_asignatura__asignatura"
        ).distinct().count()


    def get_carreras(self, obj):
        """
        Devuelve lista de carreras (id, nombre) relacionadas al docente
        por las designaciones -> comision -> asignatura -> planes_de_estudio -> carrera.
        """
        from django.db.models import Q
        from django.utils import timezone
        hoy = timezone.now()
        # obtenemos PlanDeEstudio relacionados con asignaturas que tienen comisiones con designaciones del docente
        planes_qs = models.PlanDeEstudio.objects.filter(
            # La ruta corregida:
            Q(planasignatura__comisiones__designaciones__fecha_fin__isnull=True) |
            Q(planasignatura__comisiones__designaciones__fecha_fin__gt=hoy),
            planasignatura__comisiones__designaciones__docente=obj,
            
            # Solo de planes vigentes
            esta_vigente=True,
            
            # Solo de designaciones activAS
            planasignatura__comisiones__designaciones__activo=True,            
            
        ).distinct().select_related('carrera')

        # convertir a lista de dicts con id/nombre de carrera (distinct)
        carreras = []
        seen = set()
        for plan in planes_qs:
            c = plan.carrera
            if c and c.id not in seen:
                seen.add(c.id)
                carreras.append({"id": c.id, "nombre": c.nombre})
        return carreras

    def get_designaciones(self, obj):
        """Devuelve designaciones actuales e históricas del docente."""
        from gestion_academica.serializers.M3_designaciones_docentes import DesignacionSerializer

        designaciones_qs = models.Designacion.objects.filter(docente=obj)

        actuales = designaciones_qs.filter(fecha_fin__isnull=True)
        historicas = designaciones_qs.filter(fecha_fin__isnull=False)

        return {
            "actuales": DesignacionSerializer(actuales, many=True).data,
            "historicas": DesignacionSerializer(historicas, many=True).data
        }
