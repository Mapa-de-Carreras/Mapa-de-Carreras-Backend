# gestion_academica/views/M2_gestion_docentes.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404

from gestion_academica import models
from gestion_academica.serializers.M2_gestion_docentes import DocenteSerializer


class DocenteViewSet(viewsets.ModelViewSet):
    '''Viewset para gestionar docente'''
    queryset = models.Docente.objects.all().order_by("id")
    serializer_class = DocenteSerializer
    permission_classes = [IsAuthenticated]

    def _user_can_manage_docentes(self, user):
        # verifica si el usuario tiene rol de admin o coordinador
        return user.roles.filter(
            nombre__in=["Admin", "Coordinador"]).exists()

    def create(self, request, *args, **kwargs):
        user = request.user

        # verificacion de permisos
        if not user.is_authenticated:
            raise PermissionDenied("Debe iniciar sesión para crear docentes.")
        if not (user.is_superuser or self._user_can_manage_docentes(user)):
            raise PermissionDenied("No tiene permisos para crear docentes.")

        # PRIMERA opcion: se crea un docente con los datos de un usuario ya existente
        # usuario_id = request.data.get("usuario_id")

        # if usuario_id:
        #     usuario = get_object_or_404(models.Usuario, id=usuario_id)

        #     # opcional: no permitir crear docente si el usuario no esta activo
        #     # if not usuario.is_active:
        #     #     return Response(
        #     #         {"detail": "El usuario debe activar su cuenta antes de ser asignado como docente."},
        #     #         status=status.HTTP_400_BAD_REQUEST
        #     #     )

        #     # si ya es un docente, no se puede voler a asignar
        #     if hasattr(usuario, "docente"):
        #         return Response(
        #             {"detail": "El usuario ya es docente registrado."},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )

        #     # se crea un docente a partir del usuario existente
        #     try:
        #         with transaction.atomic():
        #             docente = models.Docente.objects.create(
        #                 usuario_ptr_id=usuario_id,  # vinculo al usuario base
        #                 modalidad_id=request.data.get("modalidad_id"),
        #                 dedicacion_id=request.data.get("dedicacion_id"),
        #                 caracter_id=request.data.get("caracter_id"),
        #                 cantidad_materias=0
        #             )

        #             serializer = self.get_serializer(docente)
        #             return Response(serializer.data, status=status.HTTP_201_CREATED)

        #     except IntegrityError as e:
        #         return Response(
        #             {"detail": f"Error de base de datos: {str(e)}"},
        #             status=status.HTTP_400_BAD_REQUEST
        #         )

        # SEGUNDA opcion: se crea un docente desde cero

        # verifica legajo unico
        legajo = request.data.get("legajo")
        if models.Usuario.objects.filter(legajo=legajo).exists():
            return Response(
                {"legajo": ["El legajo ya se encuentra registrado."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.validated_data["cantidad_materias"] = 0

        try:
            with transaction.atomic():
                instance = serializer.save()
        except Exception as e:
            # Si hay una violación por DB (ej: unique), devolver un mensaje amigable
            return Response(
                {"detail": f"Error al crear docente: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        out_serializer = self.get_serializer(instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)
