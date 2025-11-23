from django.shortcuts import get_object_or_404
from gestion_academica.models import PlanAsignatura

def obtener_plan_asignatura(pk):
    return get_object_or_404(PlanAsignatura, pk=pk)

def listar_plan_asignaturas(plan_id=None):
    if plan_id:
        return PlanAsignatura.objects.filter(plan_de_estudio_id=plan_id)
    return PlanAsignatura.objects.all()

def crear_plan_asignatura(data):
    return PlanAsignatura.objects.create(**data)

def actualizar_plan_asignatura(instance, data):
    for field, value in data.items():
        setattr(instance, field, value)
    instance.save()
    return instance

def eliminar_plan_asignatura(instance):
    instance.delete()
