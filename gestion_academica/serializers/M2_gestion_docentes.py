# gestion_academica/serializers/M2_gestion_docentes.py

from rest_framework import serializers
from gestion_academica import models


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
            "horas_max_actual", "horas_min_actual", "activo",
            "max_asignaturas"
        ]


class UsuarioLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Usuario
        fields = [
            "id", "username", "first_name", "last_name",
            "email", "legajo", "celular"
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
                            "caracter", "dedicacion", "usuario", "carreras"]

    def get_carreras(self, obj):
        """
        Devuelve lista de carreras (id, nombre) relacionadas al docente
        por las designaciones -> comision -> asignatura -> planes_de_estudio -> carrera.
        """
        # obtenemos PlanDeEstudio relacionados con asignaturas que tienen comisiones con designaciones del docente
        planes_qs = models.PlanDeEstudio.objects.filter(
            planasignatura__asignatura__comisiones__designaciones__docente=obj,
            esta_vigente=True
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
    modalidad = serializers.StringRelatedField()
    dedicacion = serializers.StringRelatedField()
    caracter = serializers.StringRelatedField()

    # Se traen las designaciones relacionadas
    designaciones = serializers.SerializerMethodField()

    class Meta:
        model = models.Docente
        fields = [
            "id", "legajo", "username", "first_name", "last_name", "email",
            "celular", "modalidad", "dedicacion", "caracter", "cantidad_materias",
            "designaciones"
        ]

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
