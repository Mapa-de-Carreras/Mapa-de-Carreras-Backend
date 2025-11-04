from gestion_academica.models import Carrera
from django.shortcuts import get_object_or_404

def listar_carreras(vigentes=None, instituto_id=None):
    """Retorna todas las carreras filtradas opcionalmente por vigencia e instituto."""
    queryset = Carrera.objects.select_related('instituto').all()

    if vigentes is not None:
        queryset = queryset.filter(esta_vigente=vigentes)

    if instituto_id is not None:
        queryset = queryset.filter(instituto__id=instituto_id)

    return queryset

def obtener_carrera(pk):
    """Obtiene una carrera por su ID."""
    return get_object_or_404(Carrera, pk=pk)

def crear_carrera(validated_data):
    """Crea una nueva carrera."""
    return Carrera.objects.create(**validated_data)

def actualizar_carrera(pk, validated_data):
    """Actualiza los datos de una carrera existente."""
    carrera = get_object_or_404(Carrera, pk=pk)
    for key, value in validated_data.items():
        setattr(carrera, key, value)
    carrera.save()
    return carrera

def eliminar_carrera(pk):
    """Elimina (borrado lógico) una carrera."""
    carrera = get_object_or_404(Carrera, pk=pk)
    carrera.esta_vigente = False
    carrera.save()
    return carrera
