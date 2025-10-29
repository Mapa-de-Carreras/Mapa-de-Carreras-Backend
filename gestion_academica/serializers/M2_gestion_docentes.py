# gestion_academica/serializers/M2_gestion_docentes.py

from rest_framework import serializers
from gestion_academica import models
from gestion_academica.serializers.M3_designaciones_docentes import DesignacionSerializer


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


class DocenteSerializer(serializers.ModelSerializer):
    # permite que se envie password al crear/editar un docente
    password = serializers.CharField(write_only=True, required=False)

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

    # representaciones en lectura (simple PKs)
    modalidad = ModalidadSerializer(read_only=True)
    caracter = CaracterSerializer(read_only=True)
    dedicacion = DedicacionSerializer(read_only=True)

    class Meta:
        model = models.Docente
        # hereda todos los campos de Usuario mas los suyos
        fields = [
            "id", "username", "legajo", "first_name", "last_name", "email", "celular",
            "modalidad", "modalidad_id", "caracter", "caracter_id",
            "dedicacion", "dedicacion_id", "cantidad_materias",
            "password"
        ]

        read_only_fields = ["modalidad", "caracter", "dedicacion"]

    def create(self, validated_data):
        """
        Crea un nuevo Docente (que también es un Usuario) de forma segura.
        """
        password = validated_data.pop("password", None)

        # validar campos mínimos
        if not validated_data.get('username') or not password:
            raise serializers.ValidationError(
                {"detail": "username y password son requeridos para crear docente."})

        # aseguramos valores no-None para campos string
        first_name = validated_data.get('first_name') or ""
        last_name = validated_data.get('last_name') or ""
        email = validated_data.get('email') or ""
        legajo = validated_data.get('legajo') or ""
        celular = validated_data.get("celular") or ""

        docente = models.Docente.objects.create_user(
            username=validated_data.get('username'),
            password=password,
            legajo=legajo,
            first_name=first_name,
            last_name=last_name,
            email=email,
            celular=celular,
            modalidad=validated_data.get('modalidad'),
            caracter=validated_data.get('caracter'),
            dedicacion=validated_data.get('dedicacion')
        )

        return docente

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
        designaciones_qs = models.Designacion.objects.filter(docente=obj)

        actuales = designaciones_qs.filter(fecha_fin__isnull=True)
        historicas = designaciones_qs.filter(fecha_fin__isnull=False)

        return {
            "actuales": DesignacionSerializer(actuales, many=True).data,
            "historicas": DesignacionSerializer(historicas, many=True).data
        }
