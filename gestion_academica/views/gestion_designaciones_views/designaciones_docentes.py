# gestion_academica/views/designaciones_docentes.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from datetime import date, time, datetime, timezone
from django.utils import timezone as dj_timezone

from gestion_academica import models
from gestion_academica.permissions.coordinador_permissions import EsCoordinadorDeCarrera
from gestion_academica.serializers.M3_designaciones_docentes import DesignacionSerializer


class DesignacionViewSet(viewsets.ModelViewSet):
    queryset = models.Designacion.objects.all().order_by("id")
    serializer_class = DesignacionSerializer
    permission_classes = [IsAuthenticated, EsCoordinadorDeCarrera]

    # cargos primarios que una asignatura debe tener, al menos una
    REQUIRED_PRIMARY = {"titular", "asociado", "adjunto"}
    OPTIONAL_CARGOS = {"asistente principal",
                       "asistente de 1ra",
                       "asistente de 2da",
                       "viajero",
                       "contratado"}

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
        Si el user es Coordinador devuelve la instancia Coordinador (subclase de Usuario)
        o None si no se encuentra.
        """
        try:
            return models.Coordinador.objects.filter(usuario=user).first()
        except Exception:
            return None

    def get_queryset(self):
        """
        Filtra el queryset base.
        - Admin: Ve todas las designaciones.
        - Coordinador: Ve SÓLO las designaciones de sus carreras activas.
        """
        user = self.request.user
        qs = models.Designacion.objects.all().order_by("id")

        if user.is_superuser or user.roles.filter(nombre__iexact="Admin").exists():
            return qs

        if user.roles.filter(nombre__iexact="Coordinador").exists():
            coord_perfil = self._coordinador_de_usuario(user)
            if coord_perfil:
                carreras_activas_qs = coord_perfil.carreras_coordinadas.filter(
                    carreracoordinacion__coordinador=coord_perfil,
                    carreracoordinacion__activo=True
                )
                
                # --- AQUÍ ESTABA EL ERROR ---
                # La ruta de tu DesignacionViewSet (de la consulta anterior)
                # era incorrecta. Debe seguir tus nuevos modelos:
                # Designacion -> Comision -> PlanAsignatura -> PlanDeEstudio -> Carrera
                return qs.filter(
                    comision__plan_asignatura__plan_de_estudio__carrera__in=carreras_activas_qs
                ).distinct()

        return models.Designacion.objects.none()

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
        Crea una designacion.
        Toda la lógica de validación (solapamientos) y negocio
        (advertencia de carga horaria) está delegada al Serializer.
        """        
        # Pasamos el 'context' para que el serializer
        # pueda acceder a 'request.user'
        user = request.user

        if not (user.is_superuser or user.roles.filter(nombre__iexact="Admin").exists()):
            try:
                comision_id = request.data.get("comision_id")
                if not comision_id:
                    raise PermissionDenied("Falta el ID de la comisión.")
                
                # Buscamos la comisión (asegurándonos de que exista)
                comision = models.Comision.objects.select_related(
                    'plan_asignatura__plan_de_estudio__carrera'
                ).get(pk=comision_id)
                
                carrera_de_la_comision = comision.plan_asignatura.plan_de_estudio.carrera
                coord_perfil = self._coordinador_de_usuario(user)
                
                # Verificamos si el coordinador tiene esta carrera como activa
                if not coord_perfil.carreras_coordinadas.filter(
                        pk=carrera_de_la_comision.pk,
                        carreracoordinacion__coordinador=coord_perfil,
                        carreracoordinacion__activo=True
                    ).exists():
                    # Si no la tiene, denegamos el permiso
                    raise PermissionDenied("No tiene permiso para crear designaciones en esta carrera.")

            except models.Comision.DoesNotExist:
                return Response({"detail": f"La comisión (id={comision_id}) no existe."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            # El .save() llama al 'create' del serializer
            serializer.save()
        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Captura errores del .save() o ._verificar_...
            return Response({"detail": f"Error del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # El serializer.data contendrá la 'advertencia' si se generó
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # --- UPDATE ---
    def _handle_update(self, request, partial=False):
        """
        Logica para actualizar una designacion.
        Toda la lógica de validación (solapamientos) y negocio
        (advertencia de carga horaria) está delegada al Serializer.
        """
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            # El .save() llama al 'update' del serializer
            serializer.save()
        except IntegrityError as e:
            return Response({"detail": f"Error de base deatos: {str(e)}"}, status=status.HTTP_4D00_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return self._handle_update(request, partial=False)

    def partial_update(self, request, *args, **kwargs):
        return self._handle_update(request, partial=True)

    def _asignatura_tiene_cargo_primary_si_excluyo(self, comision, excluir_designacion_pk=None):
        """
        Verifica si la asignatura asociada a 'comision' seguirá teniendo al menos
        una designación activa con cargo en PRIMARY_CARGOS si excluimos la designación
        con pk = excluir_designacion_pk (útil antes de cerrar/eliminar).
        """
        asignatura = comision.plan_asignatura.asignatura
        qs = models.Designacion.objects.filter(
            comision__plan_asignatura__asignatura=asignatura,
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
        Implementación: Finaliza una designación activa (activo=True)
        estableciendo su fecha_fin = hoy() y activo = False.
        Si la designación ya está inactiva (activo=False), devuelve un error 400.
        """
        instance = self.get_object()
        if not instance.activo:
            return Response({"detail": "La designación ya está inactiva."},
                            status=status.HTTP_400_BAD_REQUEST)

        # verificar que al cerrar esta designación la asignatura mantenga al menos un cargo primario
        # if not self._asignatura_tiene_cargo_primary_si_excluyo(instance.comision, excluir_designacion_pk=instance.pk):
        #     return Response(
        #         {"detail": "No es posible finalizar esta designación: dejaría a la asignatura sin ningún docente con cargo Titular/Asociado/Adjunto."},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

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
