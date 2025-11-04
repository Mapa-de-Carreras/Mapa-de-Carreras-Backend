# gestion_academica/services/plan_de_estudio_service.py

from rest_framework.exceptions import ValidationError, NotFound
from gestion_academica import models

def listar_planes():
    return models.PlanDeEstudio.objects.select_related("carrera", "resolucion", "documento").prefetch_related("asignaturas")

def obtener_plan(pk):
    try:
        return models.PlanDeEstudio.objects.get(pk=pk)
    except models.PlanDeEstudio.DoesNotExist:
        raise NotFound("Plan de estudios no encontrado.")

def crear_plan(data, usuario):
    plan = models.PlanDeEstudio.objects.create(creado_por=usuario, **data)
    return plan

def actualizar_plan(pk, data):
    plan = obtener_plan(pk)
    for attr, value in data.items():
        setattr(plan, attr, value)
    plan.save()
    return plan

def eliminar_plan(pk):
    plan = obtener_plan(pk)
    # Verificar si hay asignaturas asociadas
    if plan.asignaturas.exists():
        raise ValidationError("No se puede eliminar el plan porque tiene asignaturas asociadas.")
    plan.delete()
    return True
