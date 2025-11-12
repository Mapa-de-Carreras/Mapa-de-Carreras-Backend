from rest_framework import permissions
from gestion_academica.models import (
    Coordinador,
    CarreraCoordinacion,
    Carrera,
    PlanDeEstudio,
    Comision,
    Designacion
)
from rest_framework import serializers



class EsCoordinadorDeCarrera(permissions.BasePermission):
    
   def has_permission(self, request, view):
        """
        Comprueba si el usuario está autenticado y tiene
        un perfil de Coordinador activo.
        """
        usuario = request.user
        
        return (
            usuario.is_authenticated and
            hasattr(usuario, 'coordinador') and
            usuario.coordinador.activo
        )