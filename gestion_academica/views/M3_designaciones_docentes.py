# gestion_academica/views/M3_designaciones_docentes.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from datetime import date

from gestion_academica import models
from gestion_academica.serializers.M3_designaciones_docentes import DesignacionSerializer


class DesignacionViewSet(viewsets.ModelViewSet):
    queryset = models.Designacion.objects.all().order_by("id")
    serializer_class = DesignacionSerializer
    permission_classes = [IsAuthenticated]

    # cargos primarios que una asignatura debe tener, al menos una
    PRIMARY_CARGOS = {"Titular", "Asociado", "Adjunto"}

    def _user_can_manage(self, user):
        return user.is_superuser or user.roles.filter(nombre__in=["Admin", "Coordinador"]).exists()

    def _ensure_manage_permission(self, user):
        if not self._user_can_manage(user):
            raise PermissionDenied(
                "No tiene permisos para gestionar designaciones.")

    def _periodos_solapan(self, a_start, a_end, b_start, b_end):
        """
        Devuelve True si los intervalos [a_start,a_end] y [b_start,b_end] se solapan.
        Tratamiento: si end es None se considera abierto hasta date.max.
        """
        if a_end is None:
            a_end = date.max
        if b_end is None:
            b_end = date.max
        return not (a_end < b_start or b_end < a_start)

    def _buscar_regimen_activo(self, modalidad, dedicacion):
        return models.ParametrosRegimen.objects.filter(
            modalidad=modalidad, dedicacion=dedicacion, activo=True
        ).first()

    def _coordinador_de_usuario(self, user):
        """
        Si el user es Coordinador devuelve la instancia Coordinador (subclase de Usuario)
        o None si no se encuentra.
        """
        try:
            return models.Coordinador.objects.get(pk=user.pk)
        except models.Coordinador.DoesNotExist:
            return None
        except Exception:
            return None

    def _asignatura_tiene_cargo_primary_si_excluyo(self, comision, excluir_designacion_pk=None):
        """
        Verifica si la asignatura asociada a 'comision' seguirá teniendo al menos
        una designación activa con cargo en PRIMARY_CARGOS si excluimos la designación
        con pk = excluir_designacion_pk (útil antes de cerrar/eliminar).
        """
        asignatura = comision.asignatura
        qs = models.Designacion.objects.filter(
            comision__asignatura=asignatura,
            fecha_fin__isnull=True
        )
        if excluir_designacion_pk:
            qs = qs.exclude(pk=excluir_designacion_pk)

        # comprobar existencia de al menos una designación activa con cargo primario
        return qs.filter(cargo__nombre__in=self.PRIMARY_CARGOS).exists()

    def list(self, request, *args, **kwargs):
        """
        Lista las designaciones
        """
        user = request.user
        qs = self.get_queryset()

        # si es coordinador, tratamos de limitar por carrera asociada al coordinador.
        if user.roles.filter(nombre__iexact="Coordinador").exists():
            coord = self._coordinador_de_usuario(user)
            if coord:
                # filtrar designaciones cuya asignatura pertenece a la carrera del coordinador.
                qs = qs.filter(
                    comision__asignatura__plan_asignatura__carrera=coord.carrera)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Crea una designacion
        """
        user = request.user
        self._ensure_manage_permission(user)

        data = request.data.copy()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        docente = serializer.validated_data["docente"]
        comision = serializer.validated_data["comision"]
        cargo = serializer.validated_data["cargo"]
        fecha_inicio = serializer.validated_data["fecha_inicio"]
        fecha_fin = serializer.validated_data["fecha_fin"]

        # evitar duplicado/solapamiento en misma comisión
        qs_misma_comision = models.Designacion.objects.filter(
            docente=docente, comision=comision)
        for d in qs_misma_comision:
            if self._periodos_solapan(d.fecha_inicio, d.fecha_fin, fecha_inicio, fecha_fin):
                return Response(
                    {"detail": "Solapamiento detectado con otra designación en la misma comisión."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # evitar solape de mismo cargo para el mismo docente
        qs_mismo_cargo = models.Designacion.objects.filter(
            docente=docente, cargo=cargo
        )
        for d in qs_mismo_cargo:
            if self._periodos_solapan(d.fecha_inicio, d.fecha_fin, fecha_inicio, fecha_fin):
                return Response(
                    {"detail": f"Solapamiento detectado para el cargo '{cargo.nombre}' del docente."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # dedicacion requerida
        dedicacion_obj = serializer.validated_data.get('dedicacion')
        modalidad_obj = serializer.validated_data.get(
            "modalidad") or docente.modalidad

        if dedicacion_obj is None:
            return Response(
                {"detail": "La dedicación es obligatoria para crear una designación."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if modalidad_obj is None:
            return Response(
                {"detail": "No se pudo determinar la modalidad: el docente debe tener modalidad asignada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # buscar ParametrosRegimen activo para (modalidad, dedicacion)
        regimen_obj = serializer.validated_data.get("regimen")
        if regimen_obj is None:
            regimen_obj = self._buscar_regimen_activo(
                modalidad_obj, dedicacion_obj)
            if regimen_obj is None:
                return Response(
                    {"detail": "No existe un parámetro de régimen activo para la modalidad del docente y la dedicación indicada."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # advertencia por sobrecarga, NO impide creación
        actuales = models.Designacion.objects.filter(
            docente=docente, fecha_fin__isnull=True).count()
        warning = None
        if regimen_obj and actuales >= regimen_obj.max_asignaturas:
            warning = f"Advertencia: el docente tiene {actuales} designaciones activas; máximo según régimen: {regimen_obj.max_asignaturas}."

        try:
            with transaction.atomic():
                # guardar con creado_por = request.user
                instance = serializer.save(
                    creado_por=user, regimen=regimen_obj, dedicacion=dedicacion_obj, modalidad=modalidad_obj)
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        out = self.get_serializer(instance).data
        # se advierte ante la carga maxima del docente
        if warning:
            out["warning"] = warning

        return Response(out, status=status.HTTP_201_CREATED)

    def _actualizar_designacion(self, request, partial=False):
        """
        Logica para actualizar una designacion
        """
        user = request.user
        self._ensure_manage_permission(user)

        instance = self.get_object()
        data = request.data.copy()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        docente = serializer.validated_data.get("docente", instance.docente)
        comision = serializer.validated_data.get("comision", instance.comision)
        cargo = serializer.validated_data.get("cargo", instance.cargo)
        fecha_inicio = serializer.validated_data.get(
            "fecha_inicio", instance.fecha_inicio)
        fecha_fin = serializer.validated_data.get(
            "fecha_fin", instance.fecha_fin)

        # evitar duplicado/solapamiento en misma comisión
        qs_misma_comision = models.Designacion.objects.filter(
            docente=docente, comision=comision).exclude(pk=instance.pk)
        for d in qs_misma_comision:
            if self._periodos_solapan(d.fecha_inicio, d.fecha_fin, fecha_inicio, fecha_fin):
                return Response({"detail": "Solapamiento detectado con otra designación en la misma comisión."},
                                status=status.HTTP_400_BAD_REQUEST)

        # evitar solapamiento de cargo (excluyendo esta instancia)
        qs_cargo = models.Designacion.objects.filter(
            docente=docente, cargo=cargo).exclude(pk=instance.pk)
        for d in qs_cargo:
            if self._periodos_solapan(d.fecha_inicio, d.fecha_fin, fecha_inicio, fecha_fin):
                return Response({"detail": f"Solapamiento detectado para el cargo '{cargo.nombre}'."},
                                status=status.HTTP_400_BAD_REQUEST)

        # si no se envia el regimen, se mantiene
        dedicacion_obj = serializer.validated_data.get(
            "dedicacion", getattr(instance, "dedicacion", None))
        modalidad_obj = serializer.validated_data.get(
            "modalidad", getattr(instance, "modalidad", None))
        regimen_obj = serializer.validated_data.get(
            "regimen", getattr(instance, "regimen", None))

        if regimen_obj is None:
            regimen_obj = self._buscar_regimen_activo(
                modalidad_obj, dedicacion_obj)
            if regimen_obj is None:
                return Response({"detail": "No existe un parámetro de régimen activo para la modalidad/dedicación indicada."},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                updated = serializer.save(regimen=regimen_obj)
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self.get_serializer(updated).data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """
        Permite actualizar una designacion
        """
        return self._actualizar_designacion(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        """
        Permite actualizar parcialmente una designacion
        """
        return self._actualizar_designacion(request, partial=True)

    def destroy(self, request, *args, **kwargs):
        """
        No hacemos hard delete para conservar historial.
        Implementación: si fecha_fin es NULL -> la cerramos poniendo fecha_fin = today().
        Si ya tiene fecha_fin -> devolvemos 400 indicando que ya está finalizada.
        """
        user = request.user
        self._ensure_manage_permission(user)

        instance = self.get_object()
        if instance.fecha_fin is not None:
            return Response({"detail": "La designación ya tiene fecha de fin (ya finalizada)."},
                            status=status.HTTP_400_BAD_REQUEST)

        # verificar que al cerrar esta designación la asignatura mantenga al menos un cargo primario
        if not self._asignatura_tiene_cargo_primary_si_excluyo(instance.comision, excluir_designacion_pk=instance.pk):
            return Response(
                {"detail": "No es posible finalizar esta designación: dejaría a la asignatura sin ningún docente con cargo Titular/Asociado/Adjunto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                instance.fecha_fin = date.today()
                instance.save()
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "Designación finalizada correctamente (fecha_fin establecida)."}, status=status.HTTP_200_OK)
