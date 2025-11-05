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


def eliminar_plan(pk):
    plan = obtener_plan(pk)
    if plan.asignaturas.exists():
        raise ValidationError("No se puede eliminar el plan porque tiene asignaturas asociadas.")
    plan.delete()
    return True
