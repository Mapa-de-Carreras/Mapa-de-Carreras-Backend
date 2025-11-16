# gestion_academica/services/plan_de_estudio_service.py

from rest_framework.exceptions import ValidationError, NotFound
from gestion_academica import models
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404


def listar_planes():
    return models.PlanDeEstudio.objects.select_related("carrera", "documento").prefetch_related("asignaturas")

def obtener_plan(pk):
    try:
        return models.PlanDeEstudio.objects.get(pk=pk)
    except models.PlanDeEstudio.DoesNotExist:
        raise NotFound("Plan de estudios no encontrado.")
    
    
def validar_asignatura_en_plan(plan, asignatura):
    """
    Devuelve el PlanAsignatura si la asignatura pertenece al plan.
    """
    try:
        return models.PlanAsignatura.objects.get(
            plan_de_estudio=plan,
            asignatura=asignatura
        )
    except models.PlanAsignatura.DoesNotExist:
        raise NotFound("La asignatura no pertenece a este plan de estudio.")
               


def _desactivar_planes_anteriores(carrera_id, excluir_plan_id=None):
    """
    Desactiva todos los planes vigentes de una carrera, excepto el plan indicado.
    """
    filtros = {"carrera_id": carrera_id, "esta_vigente": True}
    if excluir_plan_id:
        filtros["id__ne"] = excluir_plan_id
    models.PlanDeEstudio.objects.filter(carrera_id=carrera_id, esta_vigente=True).exclude(id=excluir_plan_id).update(esta_vigente=False)


def crear_plan(data, usuario):
    """
    Crea un nuevo plan y asegura que solo haya uno vigente por carrera.
    """
    carrera = data.get("carrera")
    esta_vigente = data.get("esta_vigente", True)

    # Si se marca vigente, desactivar los anteriores
    if carrera and esta_vigente:
        _desactivar_planes_anteriores(carrera.id)

    plan = models.PlanDeEstudio.objects.create(creado_por=usuario, **data)
    return plan


def actualizar_plan(pk, data):
    """
    Actualiza los datos de un plan existente y valida reglas de vigencia.
    """
    plan = obtener_plan(pk)
    carrera = data.get("carrera", plan.carrera)
    nueva_vigencia = data.get("esta_vigente", plan.esta_vigente)

    # Si se vuelve vigente y pertenece a una carrera, desactivar los otros
    if carrera and nueva_vigencia:
        _desactivar_planes_anteriores(carrera.id, excluir_plan_id=plan.id)

    for attr, value in data.items():
        setattr(plan, attr, value)
    plan.save()
    return plan


def cambiar_vigencia(pk, nueva_vigencia: bool):
    """
    Cambia la vigencia de un Plan de Estudio y desactiva los demás si es necesario.
    """
    plan = obtener_plan(pk)

    if nueva_vigencia:
        if not plan.carrera:
            raise ValidationError("No se puede activar un plan sin carrera asociada.")
        _desactivar_planes_anteriores(plan.carrera.id, excluir_plan_id=plan.id)

    plan.esta_vigente = nueva_vigencia
    plan.save(update_fields=["esta_vigente", "updated_at"])
    return plan

def asociar_asignatura_a_plan(validated_data):
    """Asocia una asignatura a un plan de estudio."""
    return models.PlanAsignatura.objects.create(**validated_data)

def desasociar_asignatura_de_plan(plan_id, asignatura_id):
    """Elimina la relación entre una asignatura y un plan de estudio."""
    try:
        plan_asignatura = models.PlanAsignatura.objects.get(
            plan_de_estudio_id=plan_id,
            asignatura_id=asignatura_id
        )
        plan_asignatura.delete()
        return True
    except ObjectDoesNotExist:
        return False


def eliminar_plan(pk):
    plan = obtener_plan(pk)
    if plan.asignaturas.exists():
        raise ValidationError("No se puede eliminar el plan porque tiene asignaturas asociadas.")
    plan.delete()
    return True


def listar_correlativas_por_asignatura(plan_asignatura_id: int):
    """Devuelve todas las correlativas asociadas a una asignatura del plan."""
    return models.Correlativa.objects.filter(plan_asignatura_id=plan_asignatura_id)


def crear_correlativa(validated_data):
    """Crea una correlativa si cumple las reglas."""
    correlativa = models.Correlativa.objects.create(**validated_data)
    return correlativa



def eliminar_correlativa(pk: int):
    """Elimina una correlativa por su ID."""
    correlativa = get_object_or_404(models.Correlativa, pk=pk)
    correlativa.delete()
    return correlativa
