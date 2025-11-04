from gestion_academica.models import Instituto
from django.shortcuts import get_object_or_404
from django.db.models import ProtectedError
from rest_framework.exceptions import ValidationError, NotFound


def listar_institutos():
    return Instituto.objects.all().order_by('nombre')

def obtener_instituto(id):
    return get_object_or_404(Instituto, id=id)

def crear_instituto(datos):
    instituto = Instituto.objects.create(**datos)
    return instituto

def actualizar_instituto(id, datos):
    instituto = obtener_instituto(id)
    for campo, valor in datos.items():
        setattr(instituto, campo, valor)
    instituto.save()
    return instituto

def eliminar_instituto(pk):
    """
    Elimina un instituto si no tiene dependencias activas (como carreras).
    Lanza errores controlados si no se puede eliminar.
    """
    try:
        instituto = Instituto.objects.get(pk=pk)
    except Instituto.DoesNotExist:
        raise NotFound(detail="Instituto no encontrado.")

    try:
        instituto.delete()
    except ProtectedError:
        raise ValidationError(
            detail="No se puede eliminar el instituto porque tiene carreras asociadas."
        )
