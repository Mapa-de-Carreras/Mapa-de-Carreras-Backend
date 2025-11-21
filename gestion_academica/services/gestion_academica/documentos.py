from django.shortcuts import get_object_or_404
from gestion_academica.models import Documento


def listar_documentos():
    return Documento.objects.all()


def crear_documento(data):
    return Documento.objects.create(**data)


def obtener_documento(pk):
    return get_object_or_404(Documento, pk=pk)


def actualizar_documento(documento, data):
    for key, value in data.items():
        setattr(documento, key, value)
    documento.save()
    return documento


def eliminar_documento(documento):
    documento.delete()
