from rest_framework import permissions
from rest_framework import serializers
from gestion_academica.models import Coordinador, CarreraCoordinacion


class EsCoordinadorDeCarrera(permissions.BasePermission):
    """
    Permite editar solo carreras que el usuario coordina actualmente.
    """

    carreras_coordinadas = serializers.SerializerMethodField()

    def has_permission(self, request, view):
        usuario = request.user
        return usuario.is_authenticated and usuario.roles.filter(nombre__iexact="COORDINADOR").exists()

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        
        if not usuario.is_authenticated:
            return False
        
        try:
            coordinador = Coordinador.objects.get(id=usuario.id)
        except Coordinador.DoesNotExist:
            return False

        return CarreraCoordinacion.objects.filter(
            carrera=obj,
            coordinador=coordinador,
            activo=True
        ).exists()

