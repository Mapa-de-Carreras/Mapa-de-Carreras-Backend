from rest_framework import serializers


class DocentesPorCategoriaSerializer(serializers.Serializer):
    categoria = serializers.CharField()
    total = serializers.IntegerField()


class HorasPorDocenteSerializer(serializers.Serializer):
    docente_id = serializers.IntegerField(source="docente__id")
    nombre = serializers.CharField(source="docente__usuario__first_name")
    apellido = serializers.CharField(source="docente__usuario__last_name")
    dedicacion = serializers.CharField(source="docente__dedicacion__nombre")
    modalidad = serializers.CharField(source="docente__modalidad__nombre")
    total_horas = serializers.IntegerField()
    asignaturas = serializers.IntegerField()
    estado_carga = serializers.CharField()


class DesignacionCarreraSerializer(serializers.Serializer):
    docente = serializers.CharField()
    asignatura = serializers.CharField()
    comision = serializers.CharField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField(allow_null=True)
    modalidad = serializers.CharField(allow_null=True)
    dedicacion = serializers.CharField(allow_null=True)


class HistorialDocenteSerializer(serializers.Serializer):
    asignatura = serializers.CharField()
    comision = serializers.CharField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField(allow_null=True)
    modalidad = serializers.CharField(allow_null=True)
    dedicacion = serializers.CharField(allow_null=True)

