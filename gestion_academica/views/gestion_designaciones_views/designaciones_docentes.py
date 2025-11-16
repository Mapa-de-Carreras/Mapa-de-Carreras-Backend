# gestion_academica/views/designaciones_docentes.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from datetime import date, time, datetime, timezone
from django.utils import timezone as dj_timezone

from gestion_academica import models
from gestion_academica.serializers.M3_designaciones_docentes import DesignacionSerializer


class DesignacionViewSet(viewsets.ModelViewSet):
    queryset = models.Designacion.objects.all().order_by("id")
    serializer_class = DesignacionSerializer
    permission_classes = [IsAuthenticated]

    # cargos primarios que una asignatura debe tener, al menos una
    REQUIRED_PRIMARY = {"titular", "asociado", "adjunto"}
    OPTIONAL_CARGOS = {"asistente principal",
                       "asistente de 1ra",
                       "asistente de 2da",
                       "viajero",
                       "contratado"}

    def _user_can_manage(self, user):
        """Retorna True si el usuario es superuser o tiene rol Admin/Coordinador."""
        return user.is_superuser or user.roles.filter(nombre__in=["Admin", "Coordinador"]).exists()

    def _ensure_manage_permission(self, user):
        if not self._user_can_manage(user):
            raise PermissionDenied(
                "No tiene permisos para gestionar designaciones.")

    def _periodos_solapan(self, a_start, a_end, b_start, b_end):
        """
        Devuelve True si los intervalos [a_start,a_end] y [b_start,b_end] se solapan.
        - si end es None se considera abierto hasta date.max.
        - acepta tanto date como datetime, convierte todo a datetime para comparar
        """

        def _to_aware_dt(value):
            # 1) None -> datetime.max aware (uso UTC)
            if value is None:
                return datetime.max.replace(tzinfo=timezone.utc)

            # 2) si ya es datetime
            if isinstance(value, datetime):
                # si es naive, lo hacemos aware según timezone actual
                if dj_timezone.is_naive(value):
                    return dj_timezone.make_aware(value, timezone=dj_timezone.get_current_timezone())
                return value

            # 3) si es date (pero no datetime), combínalo a 00:00:00
            if isinstance(value, date):
                dt = datetime.combine(value, time.min)
                return dj_timezone.make_aware(dt, timezone=dj_timezone.get_current_timezone())

            # 4) si es string, intentamos parsear ISO
            if isinstance(value, str):
                try:
                    # fromisoformat no acepta 'Z', convertimos a +00:00
                    s = value.replace("Z", "+00:00")
                    parsed = datetime.fromisoformat(s)
                    if dj_timezone.is_naive(parsed):
                        return dj_timezone.make_aware(parsed, timezone=dj_timezone.get_current_timezone())
                    return parsed
                except Exception:
                    # fallback seguro: devolver datetime.max aware para no romper comparaciones
                    return datetime.max.replace(tzinfo=timezone.utc)

            # 5) cualquier otro caso -> datetime.max aware
            return datetime.max.replace(tzinfo=timezone.utc)

        a_start_dt = _to_aware_dt(a_start)
        a_end_dt = _to_aware_dt(a_end)
        b_start_dt = _to_aware_dt(b_start)
        b_end_dt = _to_aware_dt(b_end)

        return not (a_end_dt < b_start_dt or b_end_dt < a_start_dt)

    def _buscar_regimen_activo(self, modalidad, dedicacion):
        return models.ParametrosRegimen.objects.filter(
            modalidad=modalidad, dedicacion=dedicacion, activo=True
        ).first()

    def _coordinador_de_usuario(self, user):
        """
        Devuelve la instancia Coordinador asociada al `user`, o None si no existe.
        Encapsula la consulta para usarla desde otras funciones.
        """
        try:
            return models.Coordinador.objects.filter(usuario=user).first()
        except Exception:
            return None

    def get_object(self):
        obj = super().get_object()  # obtiene el objeto real

        user = self.request.user

        # Si es coordinador, verificar si pertenece a sus carreras coordinadas
        if user.roles.filter(nombre__iexact="Coordinador").exists():
            coord = models.Coordinador.objects.filter(usuario=user).first()

            if coord:
                pertenece = obj.comision.asignatura.planes_de_estudio.filter(
                    carrera__in=coord.carreras_coordinadas.all(),
                    esta_vigente=True
                ).exists()

                if not pertenece:
                    raise PermissionDenied(
                        detail="No tiene permisos para acceder a esta designación."
                    )

        return obj

    def list(self, request, *args, **kwargs):
        """
        Lista las designaciones
        - Solo los coordinadores ven las designacioens cuyas asignaturas pertenecen a las carreras que coordinan
        """
        user = request.user
        qs = self.get_queryset()

        activo_param = request.query_params.get("activo")
        if activo_param is not None:
            if activo_param.lower() in ['true', '1', 't', 'yes']:
                qs = qs.filter(activo=True)
            elif activo_param.lower() in ['false', '0', 'f', 'no']:
                qs = qs.filter(activo=False)

        # si es coordinador, limitar por sus carreras
        if user.roles.filter(nombre__iexact="Coordinador").exists():
            # obtener el objeto Coordinador asociado al usuario.
            coord = self._coordinador_de_usuario(user)
            if coord:
                carreras_qs = coord.carreras_coordinadas.all()
                # filtrar designaciones cuya asignatura pertenece a la carrera del coordinador.
                qs = qs.filter(
                    comision__asignatura__planes_de_estudio__carrera__in=carreras_qs
                ).distinct()

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Crea una designacion
        - evita solapamientos (misma comision / cargo del mimsmo docente)
        - exige modalidad (si no se recibe, se obtiene del docente)
        - busca el parametro regimen activo para (modalidad, dedicacion) si es que no se envia en la peticion
        - devuelve warning si el docente supera el max_asignaturas
        """
        user = request.user
        self._ensure_manage_permission(user)

        data = request.data.copy()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        docente = serializer.validated_data.get("docente")
        comision = serializer.validated_data.get("comision")
        cargo = serializer.validated_data.get("cargo")
        fecha_inicio = serializer.validated_data.get("fecha_inicio")
        fecha_fin = serializer.validated_data.get("fecha_fin")

        # comprobar permiso de coordinador
        if user.roles.filter(nombre__iexact="Coordinador").exists():
            # obtener el objeto Coordinador asociado al usuario.
            coord = self._coordinador_de_usuario(user)
            if coord is None:
                return Response({"detail": "Perfil de Coordinador no encontrado."}, status=status.HTTP_403_FORBIDDEN)

            # busca si existe al menos un PlanDeEstudio VIGENTE
            # para la asignatura de la comisión cuyo campo 'carrera' esté en las carreras coordinadas.
            pertenece = comision.asignatura.planes_de_estudio.filter(
                carrera__in=coord.carreras_coordinadas.all(),
                esta_vigente=True
            ).exists()
            if not pertenece:
                return Response({"detail": "No tiene permisos para crear designaciones en esa asignatura/carrera."},
                                status=status.HTTP_403_FORBIDDEN)

        # evitar duplicado/solapamiento en misma comisión (mismo docente y misma comision)
        qs_misma_comision = models.Designacion.objects.filter(
            docente=docente, comision=comision
        )
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
            "modalidad") or getattr(docente, "modalidad", None)

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

        # advertencia por sobrecarga (no impide creación)
        actuales = models.Designacion.objects.filter(
            docente=docente, activo=True).count()
        warning = None
        if regimen_obj and actuales >= regimen_obj.max_asignaturas:
            warning = f"Advertencia: el docente tiene {actuales} designaciones activas; máximo según régimen: {regimen_obj.max_asignaturas}."

        try:
            with transaction.atomic():
                # guardar con creado_por = request.user
                instance = serializer.save(
                    creado_por=user,
                    regimen=regimen_obj,
                    dedicacion=dedicacion_obj,
                    modalidad=modalidad_obj,
                    activo=True
                )
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        out = self.get_serializer(instance).data
        # se advierte ante la carga maxima del docente
        if warning:
            out["warning"] = warning

        return Response(out, status=status.HTTP_201_CREATED)

    def _handle_update(self, request, partial=False):
        """
        Logica para actualizar una designacion
        """
        user = request.user
        self._ensure_manage_permission(user)

        instance = self.get_object()
        data = request.data.copy()
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # comprobar permiso de coordinador
        if user.roles.filter(nombre__iexact="Coordinador").exists():
            # obtener el objeto Coordinador asociado al usuario.
            coord = self._coordinador_de_usuario(user)
            if coord is None:
                return Response({"detail": "Perfil de Coordinador no encontrado."}, status=status.HTTP_403_FORBIDDEN)

            # si el usuario es Coordinador también
            # se verificar que la comisión objetivo esté dentro de sus carreras.
            comision_obj = serializer.validated_data.get(
                "comision", instance.comision)

            # busca si existe al menos un PlanDeEstudio VIGENTE
            # para la asignatura de la comisión cuyo campo 'carrera' esté en las carreras coordinadas.
            pertenece = comision_obj.asignatura.planes_de_estudio.filter(
                carrera__in=coord.carreras_coordinadas.all(),
                esta_vigente=True
            ).exists()

            if not pertenece:
                return Response({"detail": "No tiene permisos para editar esa designación."},
                                status=status.HTTP_403_FORBIDDEN)

        validated = serializer.validated_data.copy()

        if 'fecha_fin' in validated:
            if validated.get('fecha_fin') is None:
                # reabrir/designacion activa
                validated['activo'] = True
            else:
                # cerrar/designacion inactiva
                validated['activo'] = False

        docente = serializer.validated_data.get("docente", instance.docente)
        comision = serializer.validated_data.get("comision", instance.comision)
        cargo = serializer.validated_data.get("cargo", instance.cargo)
        fecha_inicio = serializer.validated_data.get(
            "fecha_inicio", instance.fecha_inicio)
        fecha_fin = serializer.validated_data.get(
            "fecha_fin", instance.fecha_fin)

        # si la actualización implica cerrar la designación (fecha_fin != None)
        # debemos verificar que la asignatura mantenga al menos un cargo primario activo
        if 'fecha_fin' in validated and validated.get('fecha_fin') is not None:
            # comision ya fue resuelto arriba (puede ser new o el existing)
            # Si la comprobación falla, devolvemos 400 y no guardamos.
            if not self._asignatura_tiene_cargo_primary_si_excluyo(comision, excluir_designacion_pk=instance.pk):
                return Response(
                    {"detail": "No es posible finalizar esta designación: dejaría a la asignatura sin ningún docente con cargo Titular/Asociado/Adjunto (u otro cargo primario requerido)."},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
            'dedicacion', getattr(instance, 'dedicacion', None))
        modalidad_obj = serializer.validated_data.get('modalidad', getattr(
            instance, 'modalidad', getattr(docente, "modalidad", None)))

        if dedicacion_obj is None:
            return Response(
                {"detail": "La dedicación es obligatoria para actualizar una designación."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if modalidad_obj is None:
            return Response(
                {"detail": "No se pudo determinar la modalidad: el docente debe tener modalidad asignada."},
                status=status.HTTP_400_BAD_REQUEST
            )

        regimen_obj = serializer.validated_data.get(
            "regimen", getattr(instance, "regimen", None))

        if regimen_obj is None:
            regimen_obj = self._buscar_regimen_activo(
                modalidad_obj, dedicacion_obj)
            if regimen_obj is None:
                return Response({"detail": "No existe un parámetro de régimen activo para la modalidad/dedicación indicada."},
                                status=status.HTTP_400_BAD_REQUEST)

        # advertencia por sobrecarga: contamos designaciones activas excluyendo esta instancia si estaba activa
        actuales_qs = models.Designacion.objects.filter(
            docente=docente, activo=True).exclude(pk=instance.pk)
        actuales = actuales_qs.count()
        warning = None
        if regimen_obj and actuales >= regimen_obj.max_asignaturas:
            warning = f"Advertencia: el docente tiene {actuales} designaciones activas; máximo según régimen: {regimen_obj.max_asignaturas}."

        try:
            with transaction.atomic():
                updated = serializer.save(
                    regimen=regimen_obj,
                    dedicacion=dedicacion_obj,
                    modalidad=modalidad_obj,
                    **({'activo': validated['activo']} if 'activo' in validated else {})
                )
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        out = self.get_serializer(updated).data
        if warning:
            out["warning"] = warning
        return Response(out, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """
        Permite actualizar una designacion
        """
        return self._handle_update(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        """
        Permite actualizar parcialmente una designacion
        """
        return self._handle_update(request, partial=True)

    def _asignatura_tiene_cargo_primary_si_excluyo(self, comision, excluir_designacion_pk=None):
        """
        Verifica si la asignatura asociada a 'comision' seguirá teniendo al menos
        una designación activa con cargo en PRIMARY_CARGOS si excluimos la designación
        con pk = excluir_designacion_pk (útil antes de cerrar/eliminar).
        """
        asignatura = comision.asignatura
        qs = models.Designacion.objects.filter(
            comision__asignatura=asignatura,
            activo=True
        )
        if excluir_designacion_pk:
            qs = qs.exclude(pk=excluir_designacion_pk)

        # obtenemos los nombres de cargo activos y comparamos en lower()
        nombres = qs.values_list('cargo__nombre', flat=True)
        for nombre in nombres:
            if nombre and nombre.lower() in self.REQUIRED_PRIMARY:
                return True
        return False

    def destroy(self, request, *args, **kwargs):
        """
        No hacemos hard delete para conservar historial.
        Implementación: si fecha_fin es NULL -> la cerramos poniendo fecha_fin = today().
        Si ya tiene fecha_fin -> devolvemos 400 indicando que ya está finalizada.
        """
        user = request.user
        self._ensure_manage_permission(user)

        instance = self.get_object()
        if not instance.activo:
            return Response({"detail": "La designación ya está inactiva."},
                            status=status.HTTP_400_BAD_REQUEST)

        if user.roles.filter(nombre__iexact="Coordinador").exists():
            coord = self._coordinador_de_usuario(user)
            if coord and not instance.comision.asignatura.planes_de_estudio.filter(
                    carrera__in=coord.carreras_coordinadas.all(), esta_vigente=True).exists():
                return Response({"detail": "No tiene permisos para finalizar esta designación."},
                                status=status.HTTP_403_FORBIDDEN)

        # verificar que al cerrar esta designación la asignatura mantenga al menos un cargo primario
        if not self._asignatura_tiene_cargo_primary_si_excluyo(instance.comision, excluir_designacion_pk=instance.pk):
            return Response(
                {"detail": "No es posible finalizar esta designación: dejaría a la asignatura sin ningún docente con cargo Titular/Asociado/Adjunto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                instance.fecha_fin = dj_timezone.now()
                instance.activo = False
                instance.save()
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "Designación finalizada correctamente (fecha_fin establecida)."}, status=status.HTTP_200_OK)
