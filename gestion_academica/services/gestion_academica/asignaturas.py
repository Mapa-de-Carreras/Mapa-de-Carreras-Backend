from gestion_academica.models import Asignatura
from django.shortcuts import get_object_or_404

def listar_asignaturas(activas=None):
    """Devuelve todas las asignaturas, con posibilidad de filtrar por estado."""
    queryset = Asignatura.objects.all()
    if activas is not None:
        queryset = queryset.filter(activo=activas)
    return queryset

def obtener_asignatura(pk):
    """Obtiene una asignatura por su ID."""
    return get_object_or_404(Asignatura, pk=pk)

def crear_asignatura(validated_data):
    """Crea una nueva asignatura."""
    return Asignatura.objects.create(**validated_data)

def actualizar_asignatura(pk, validated_data):
    """Actualiza los datos de una asignatura."""
    asignatura = get_object_or_404(Asignatura, pk=pk)
    for key, value in validated_data.items():
        setattr(asignatura, key, value)
    asignatura.save()
    return asignatura

def eliminar_asignatura(pk):
    """Borrado lógico: desactiva la asignatura."""
    asignatura = get_object_or_404(Asignatura, pk=pk)
    asignatura.activo = False
    asignatura.save()
    return asignatura
