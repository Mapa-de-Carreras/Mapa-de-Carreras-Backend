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
        """
        Comprueba si el objeto (el perfil 'Coordinador') 
        que se está viendo/editando pertenece al usuario logueado.
        
        'obj' es el perfil de Coordinador.
        """
        # Si el usuario es superadmin, puede editar cualquier cosa
        if request.user.is_superuser or request.user.is_staff:
            return True
            
        # Comprueba si el 'usuario' del perfil (obj) es el
        # mismo que el 'usuario' que hace la petición.
        return obj.usuario == request.user

