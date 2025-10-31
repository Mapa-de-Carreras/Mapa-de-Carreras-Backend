from gestion_academica.models import Instituto
from django.shortcuts import get_object_or_404

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

def eliminar_instituto(id):
    instituto = obtener_instituto(id)
    instituto.delete()
    return True
