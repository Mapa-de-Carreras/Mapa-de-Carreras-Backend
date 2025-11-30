from django.db.models.signals import post_migrate
from django.dispatch import receiver

from gestion_academica import models
from gestion_academica.constants import ROLES_PREDETERMINADOS


@receiver(post_migrate)
def crear_roles_predeterminados(sender, **kwargs):
    """
    Crea los roles que el sistema necesita sí o sí, usando la lista hardcodeada.
    """
    if sender.name != "gestion_academica":
        return

    for rol_data in ROLES_PREDETERMINADOS:
        models.Rol.objects.get_or_create(
            nombre=rol_data["nombre"],
            defaults={"descripcion": rol_data.get("descripcion", "")}
        )
