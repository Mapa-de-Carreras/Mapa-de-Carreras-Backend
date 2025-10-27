# gestion_academica/views/M2_gestion_catalogos.py

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from gestion_academica import models
from gestion_academica.serializers.M2_gestion_docentes import (
    ModalidadSerializer, CaracterSerializer, DedicacionSerializer
)


class BaseAdminCoordinadorViewSet(viewsets.ModelViewSet):
    '''
    Restringe creacion/actualizacion/borrado a admin o coordinador
    '''
    permission_classes = [IsAuthenticated]

    def _user_can_manage(self, user):
        return user.is_superuser or user.roles.filter(nombre__in=["Admin", "Coordinador"]).exists()

    def create(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para crear elementos de catálogo.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para modificar elementos de catálogo.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para modificar elementos de catálogo.")
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._user_can_manage(request.user):
            raise PermissionDenied(
                "No tiene permisos para eliminar elementos de catálogo.")
        return super().destroy(request, *args, **kwargs)


# VIEWSETS para modalidad, caracteri y dedicacion
class ModalidadViewSet(BaseAdminCoordinadorViewSet):
    '''
    Listar/crear/actualizar modalidad
    '''
    queryset = models.Modalidad.objects.all().order_by("id")
    serializer_class = ModalidadSerializer


class CaracterViewSet(BaseAdminCoordinadorViewSet):
    '''
    Listar/crear/actualizar caracter
    '''
    queryset = models.Caracter.objects.all().order_by("id")
    serializer_class = CaracterSerializer


class DedicacionViewSet(BaseAdminCoordinadorViewSet):
    '''
    Listar/crear/actualizar dedicacion
    '''
    queryset = models.Dedicacion.objects.all().order_by("id")
    serializer_class = DedicacionSerializer
