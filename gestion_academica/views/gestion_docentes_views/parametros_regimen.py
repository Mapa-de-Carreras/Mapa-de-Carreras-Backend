# gestion_academica/views/M2_parametros_regimen.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404

from gestion_academica import models
from gestion_academica.serializers.M2_gestion_docentes import ParametrosRegimenSerializer


class ParametrosRegimenViewSet(viewsets.ModelViewSet):
    queryset = models.ParametrosRegimen.objects.all().order_by("id")
    serializer_class = ParametrosRegimenSerializer
    permission_classes = [IsAuthenticated]

    def _user_can_manage(self, user):
        return user.is_superuser or user.roles.filter(nombre__in=["Admin", "Coordinador"]).exists()

    def _calcular_max_asignaturas(self, dedicacion):
        nombre = dedicacion.nombre.lower()
        if nombre == "simple":
            return 2
        if nombre in ["semiexclusiva", "exclusiva"]:
            return 3

    def _validar_horas(self, data):
        """Verifica que las horas mínimas no superen las máximas."""
        hmin_sem = data.get("horas_min_frente_alumnos")
        hmax_sem = data.get("horas_max_frente_alumnos")
        hmin_anual = data.get("horas_min_actual")
        hmax_anual = data.get("horas_max_actual")

        if hmin_sem and hmax_sem and hmin_sem > hmax_sem:
            raise ValidationError(
                "Las horas mínimas semanales no pueden superar las máximas.")
        if hmin_anual and hmax_anual and hmin_anual > hmax_anual:
            raise ValidationError(
                "Las horas mínimas anuales no pueden superar las máximas.")

    def _desactivar_anteriores(self, modalidad_id, dedicacion_id):
        """Desactiva cualquier otro parámetro activo con la misma modalidad y dedicación."""
        models.ParametrosRegimen.objects.filter(
            modalidad_id=modalidad_id, dedicacion_id=dedicacion_id
        ).update(activo=False)

    def create(self, request, *args, **kwargs):
        """
        Permite crear un parámetro de régimen
        """
        user = request.user
        if not self._user_can_manage(user):
            raise PermissionDenied(
                "Solo Admin o Coordinador pueden registrar parámetros de régimen.")

        data = request.data.copy()
        modalidad_id = data.get("modalidad_id")
        dedicacion_id = data.get("dedicacion_id")

        # verificar campos obligatorios
        if not modalidad_id or not dedicacion_id:
            return Response({"detail": "Debe especificar modalidad y dedicación."},
                            status=status.HTTP_400_BAD_REQUEST)

        # obtener objetos relacionados
        modalidad = get_object_or_404(models.Modalidad, id=modalidad_id)
        dedicacion = get_object_or_404(models.Dedicacion, id=dedicacion_id)

        # calcular máximo de asignaturas según la dedicación
        data["max_asignaturas"] = self._calcular_max_asignaturas(dedicacion)

        # validar coherencia de horas
        try:
            self._validar_horas(data)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # validar y guardar
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # desactivar versiones anteriores para la misma combinación
            self._desactivar_anteriores(modalidad_id, dedicacion_id)
            instance = serializer.save(activo=True)

        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Permite actualizar un parámetro
        """
        return self._actualizar_parametro(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        """
        Permite actualizar parcialmente un parámetro
        """
        return self._actualizar_parametro(request, partial=True)

    def _actualizar_parametro(self, request, partial):
        """Logica para actualizar un parametro"""
        user = request.user
        if not self._user_can_manage(user):
            raise PermissionDenied(
                "Solo Admin o Coordinador pueden editar parámetros de régimen.")

        instance = self.get_object()
        data = request.data.copy()

        modalidad_id = data.get("modalidad_id", instance.modalidad_id)
        dedicacion_id = data.get("dedicacion_id", instance.dedicacion_id)
        dedicacion = get_object_or_404(models.Dedicacion, id=dedicacion_id)

        # calcular nuevamente el máximo de asignaturas, este atributo no se recibe del cliente
        data["max_asignaturas"] = self._calcular_max_asignaturas(dedicacion)

        # validar coherencia de horas
        try:
            self._validar_horas(data)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # validar y guardar dentro de una transacción
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # si se está activando este registro, desactivar otros
            if serializer.validated_data.get("activo", instance.activo):
                self._desactivar_anteriores(modalidad_id, dedicacion_id)

            instance = serializer.save()

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        if not self._user_can_manage(user):
            raise PermissionDenied(
                "Solo Admin o Coordinador pueden deshabilitar parámetros de régimen.")

        instance = self.get_object()

        if not instance.activo:
            return Response({"detail": "El parámetro ya se encuentra deshabilitado."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                instance.activo = False
                instance.save()
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos al deshabilitar: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado al deshabilitar: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "Parámetro deshabilitado correctamente."}, status=status.HTTP_200_OK)
