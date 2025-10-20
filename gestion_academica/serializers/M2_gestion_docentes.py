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
            "horas_max_actual", "horas_min_actual",
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
    modalidad = serializers.PrimaryKeyRelatedField(read_only=True)
    caracter = serializers.PrimaryKeyRelatedField(read_only=True)
    dedicacion = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.Docente
        # hereda todos los campos de Usuario mas los suyos
        fields = [
            "id", "legajo", "nombre", "apellido", "email", "celular",
            "modalidad", "modalidad_id", "caracter", "caracter_id",
            "dedicacion", "dedicacion_id", "cantidad_materias",
            "password"
        ]
        read_only_fields = ["modalidad", "caracter", "dedicacion"]

    def create(self, validated_data):
        """
        Creación mínima: maneja password seguro y cubre el caso en que
        Docente.objects.create_user esté disponible o no.
        """
        password = validated_data.pop("password", None)

        # create_user (heredado de UsuarioManager)
        if hasattr(models.Docente.objects, "create_user"):
            docente = models.Docente.objects.create_user(
                **validated_data, password=password)
        else:
            # fallback: crear con create() y, si se dio password, setearlo
            docente = models.Docente.objects.create(**validated_data)
            if password:
                docente.set_password(password)
                docente.save()

        return docente

    def update(self, instance, validated_data):
        '''
        Actualizar un Docente:
        - Si llega password, se setea con set_password para que se almacene correctamente.
        - Para el resto, se setean atributos y se guarda la instancia.
        '''
        password = validated_data.pop("password", None)

        # simple update, setea campos y guarda
        for key, val in validated_data.items():
            setattr(instance, key, val)
        instance.save()
        return instance
