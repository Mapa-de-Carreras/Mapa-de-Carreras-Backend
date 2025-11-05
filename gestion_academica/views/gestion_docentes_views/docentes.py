# gestion_academica/views/M2_gestion_docentes.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from gestion_academica import models
from gestion_academica.serializers.M2_gestion_docentes import DocenteSerializer, DocenteDetalleSerializer


class DocenteViewSet(viewsets.ModelViewSet):
    '''Viewset para gestionar docente'''
    queryset = models.Docente.objects.all().order_by("id")
    serializer_class = DocenteSerializer
    permission_classes = [IsAuthenticated]

    def _user_can_manage(self, user):
        return user.is_superuser or user.roles.filter(nombre__in=["Admin", "Coordinador"]).exists()

    def _ensure_manage_permission(self, user):
        if not self._user_can_manage(user):
            raise PermissionDenied(
                "No tiene permisos para gestionar docentes.")

    def _validate_unique_legajo(self, legajo, instance=None):
        qs = models.Usuario.objects.filter(legajo=legajo)
        if instance is not None:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise ValidationError(
                "El legajo ya se encuentra registrado por otro usuario.")

    def create(self, request, *args, **kwargs):
        '''
        Permite crear un docente
        '''
        user = request.user
        self._ensure_manage_permission(user)

        data = request.data.copy()

        # verifica legajo unico
        legajo = request.data.get("legajo")
        if not legajo:
            return Response({"detail": "El legajo es requerido para crear un docente."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            self._validate_unique_legajo(legajo)
        except ValidationError as e:
            return Response({"legajo": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

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

    def _handle_update(self, request, partial):
        user = request.user
        self._ensure_manage_permission(user)

        instance = self.get_object()

        # Campos permitidos
        allowed_fields = {
            "legajo", "first_name", "last_name",
            "email", "celular", "caracter_id", "modalidad_id", "dedicacion_id"
        }

        # Filtrar solo los campos válidos del request
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        if not data:
            return Response(
                {"detail": "No se enviaron campos válidos para actualizar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # si cambian legajo validar unicidad
        if "legajo" in data:
            try:
                self._validate_unique_legajo(data["legajo"], instance=instance)
            except ValidationError as e:
                return Response({"legajo": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                updated = serializer.save()
        except Exception as e:
            return Response({"detail": f"Error al actualizar docente: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        '''
        Permite actualizar un docente, solo campos permitidos
        '''
        return self._handle_update(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        '''
        Permite actualizar parcialmente un docente, solo campos permitidos
        '''
        return self._handle_update(request, partial=True)

    def destroy(self, request, *args, **kwargs):
        '''
        Permite deshabilitar un docente
        '''
        user = request.user
        self._ensure_manage_permission(user)

        instance = self.get_object()

        if not instance.is_active:
            return Response(
                {"detail": "El docente ya está deshabilitado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                instance.is_active = False
                instance.save()
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos al deshabilitar: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado al deshabilitar: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": f"Docente '{instance.username}' deshabilitado correctamente."},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        '''
        Permite visualizar el detalle completo de un docente
        '''
        user = request.user

        self._ensure_manage_permission(user)

        instance = self.get_object()

        if not instance.is_active:
            return Response(
                {"detail": "El docente está deshabilitado y no puede visualizarse."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DocenteDetalleSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
