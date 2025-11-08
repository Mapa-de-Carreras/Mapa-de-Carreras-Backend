from django.shortcuts import get_object_or_404
from gestion_academica.models import Comision


def listar_comisiones():
    return Comision.objects.all().order_by("id")


def obtener_comision(pk):
    return get_object_or_404(Comision, pk=pk)


def crear_comision(data):
    return Comision.objects.create(**data)


def actualizar_comision(pk, data):
    comision = obtener_comision(pk)
    for attr, value in data.items():
        setattr(comision, attr, value)
    comision.save()
    return comision


def eliminar_comision(pk):
    comision = obtener_comision(pk)
    comision.delete()
