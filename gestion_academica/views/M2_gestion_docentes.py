# gestion_academica/views/M2_gestion_docentes.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404

from gestion_academica import models
from gestion_academica.serializers.M2_gestion_docentes import DocenteSerializer, DocenteDetalleSerializer


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
        '''
        Permite crear un docente
        '''
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

    def update(self, request, *args, **kwargs):
        '''
        Permite actualizar un docente, solo campos permitidos
        '''
        user = request.user

        # Verificación de permisos
        if not user.is_authenticated:
            raise PermissionDenied("Debe iniciar sesión para editar docentes.")
        if not (user.is_superuser or self._user_can_manage_docentes(user)):
            raise PermissionDenied("No tiene permisos para editar docentes.")

        # Obtener el docente a editar
        docente = self.get_object()

        # Campos permitidos
        allowed_fields = [
            "legajo", "first_name", "last_name",
            "email", "celular", "caracter_id", "modalidad_id"
        ]

        # Filtrar solo los campos válidos del request
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        if not data:
            return Response(
                {"detail": "No se enviaron campos válidos para actualizar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(docente, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        '''
        Permite deshabilitar un docente
        '''
        user = request.user

        # verificacion de permisos
        if not (user.is_superuser or self._user_can_manage_docentes(user)):
            raise PermissionDenied(
                "No tiene permisos para deshabilitar docentes.")

        docente = self.get_object()

        if not docente.is_active:
            return Response(
                {"detail": "El docente ya está deshabilitado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # deshabilitacion
        with transaction.atomic():
            docente.is_active = False
            docente.save()

        return Response(
            {"detail": f"El docente '{docente.username}' fue deshabilitado correctamente."},
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, *args, **kwargs):
        '''
        Permite visualizar el detalle completo de un docente
        '''
        user = request.user

        if not (user.is_superuser or self._user_can_manage_docentes(user)):
            raise PermissionDenied(
                "No tiene permisos para visualizar docentes.")

        docente = self.get_object()

        if not docente.is_active:
            return Response(
                {"detail": "El docente está deshabilitado y no puede visualizarse."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DocenteDetalleSerializer(docente)
        return Response(serializer.data, status=status.HTTP_200_OK)
