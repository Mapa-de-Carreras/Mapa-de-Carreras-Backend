# gestion_academica/views/M2_gestion_docentes.py

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.decorators import action
from django.db import IntegrityError, transaction
from django.http import Http404

from gestion_academica import models
from gestion_academica.serializers.M2_gestion_docentes import DocenteSerializer, DocenteDetalleSerializer


class DocenteViewSet(viewsets.ModelViewSet):
    '''Viewset para gestionar docente'''
    queryset = models.Docente.objects.all().order_by("id")
    serializer_class = DocenteSerializer
    permission_classes = [IsAuthenticated]
    # El 'lookup_field' ahora debe ser 'usuario_id'
    # para que /api/docentes/7/ funcione.
    lookup_field = 'usuario__id'

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

    @action(detail=False, methods=["get"], url_path=r"carrera/(?P<carrera_id>\d+)")
    def por_carrera(self, request, carrera_id=None):
        """
        Lista docentes relacionados con la carrera indicada.
        Ruta: GET /api/docentes/carrera/{carrera_id}/
        Comportamiento actual:
          - Devuelve docentes que tienen alguna designación cuyo plan de estudio pertenece a la carrera.
          - Filtra por plan vigente (esta_vigente=True) para evitar planes antiguos.
          - Esto puede devolver el mismo docente para varias carreras si la misma asignatura
            está presente en los planes de varias carreras.

        Otra alternativa - SOLO designaciones activas:
          - Si queremos devolver solo docentes con designaciones activas,
            usar la query alternativa que aparece comentada más abajo.
        """
        user = request.user

        # base queryset: Docentes que tienen designaciones en asignaturas de la carrera
        # filtra por plan vigente para evitar duplicados por planes antiguos
        qs = models.Docente.objects.filter(
            designaciones__comision__asignatura__planes_de_estudio__carrera__id=carrera_id,
            designaciones__comision__asignatura__planes_de_estudio__esta_vigente=True
        ).distinct().order_by("id")

        # otra alternativa
        # devolver solo docentes con designación actualmente activa, para saber quien actualmente da clases.
        # qs = models.Docente.objects.filter(
        #     designaciones__comision__asignatura__planes_de_estudio__carrera__id=carrera_id,
        #     designaciones__comision__asignatura__planes_de_estudio__esta_vigente=True,
        #     designaciones__fecha_fin__isnull=True,   # <-- solo activas
        # ).distinct().order_by("id")

        # filtra por query param activo si viene
        activo_param = request.query_params.get("activo")
        if activo_param is not None:
            if activo_param.lower() in ['true', '1', 't', 'yes']:
                qs = qs.filter(activo=True)
            elif activo_param.lower() in ['false', '0', 'f', 'no']:
                qs = qs.filter(activo=False)

        # si el user es Coordinador, limitar por sus carreras
        if user.roles.filter(nombre__iexact="Coordinador").exists():
            coord = models.Coordinador.objects.filter(usuario=user).first()
            if coord:
                carreras_qs = coord.carreras_coordinadas.all()
                if not carreras_qs.filter(pk=carrera_id).exists():
                    return Response({"detail": "No tiene permisos para ver docentes de esa carrera."},
                                    status=status.HTTP_403_FORBIDDEN)

        page = self.paginate_queryset(qs)
        serializer_class = DocenteSerializer
        if page is not None:
            serializer = serializer_class(
                page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

        serializer = serializer_class(
            qs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_object(self):
        # pk es el usuario id --> /api/docentes/<usuario_id>
        pk = self.kwargs.get(self.lookup_field)

        try:
            return models.Docente.objects.get(usuario__id=pk)
        except models.Docente.DoesNotExist:
            raise Http404("No se encontro el Docente")

    # def create(self, request, *args, **kwargs):
    #     '''
    #     Permite crear un docente
    #     '''
    #     user = request.user
    #     self._ensure_manage_permission(user)

    #     data = request.data.copy()

    #     # verifica legajo unico
    #     legajo = request.data.get("legajo")
    #     if not legajo:
    #         return Response({"detail": "El legajo es requerido para crear un docente."},
    #                         status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         self._validate_unique_legajo(legajo)
    #     except ValidationError as e:
    #         return Response({"legajo": [str(e)]}, status=status.HTTP_400_BAD_REQUEST)

    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     serializer.validated_data["cantidad_materias"] = 0

    #     try:
    #         with transaction.atomic():
    #             instance = serializer.save()
    #     except Exception as e:
    #         # Si hay una violación por DB (ej: unique), devolver un mensaje amigable
    #         return Response(
    #             {"detail": f"Error al crear docente: {str(e)}"},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     out_serializer = self.get_serializer(instance)
    #     return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def create(self, request, *args, **kwargs):
        user = request.user
        self._ensure_manage_permission(user)

        data = request.data.copy()

        usuario_id = data.get("usuario_id")
        if not usuario_id:
            return Response({"usuario_id": ["El campo usuario_id es obligatorio."]},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario_obj = models.Usuario.objects.get(pk=usuario_id)
        except models.Usuario.DoesNotExist:
            return Response({"usuario_id": ["Usuario no encontrado."]},
                            status=status.HTTP_400_BAD_REQUEST)

        if hasattr(usuario_obj, "docente"):
            return Response({"detail": "El usuario ya posee un perfil Docente."},
                            status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "modalidad_id": data.get("modalidad_id"),
            "caracter_id": data.get("caracter_id"),
            "dedicacion_id": data.get("dedicacion_id"),
            "cantidad_materias": data.get("cantidad_materias", 0),
            "activo": data.get("activo", True)
        }

        # Filtrar None para que el serializer no intente validar claves nulas
        payload = {k: v for k, v in payload.items() if v is not None}

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data.copy()
        validated["usuario"] = usuario_obj

        try:
            with transaction.atomic():
                instance = models.Docente.objects.create(**validated)
                try:
                    rol_docente = models.Rol.objects.get(
                        nombre__iexact="Docente")
                    models.RolUsuario.objects.get_or_create(
                        usuario=usuario_obj, rol=rol_docente)
                except:
                    pass

        except IntegrityError as e:
            return Response({"detail": f"Error de base de datos al crear docente: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Error inesperado al crear docente: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        out_serializer = self.get_serializer(instance)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def _handle_update(self, request, partial):
        user = request.user
        self._ensure_manage_permission(user)

        instance = self.get_object()

        # Campos permitidos
        allowed_fields = {
            "cantidad_materias", "activo", "caracter_id", "modalidad_id", "dedicacion_id"
        }

        # Filtrar solo los campos válidos del request
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        if not data:
            return Response(
                {"detail": "No se enviaron campos válidos para actualizar."},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        if not instance.activo:
            return Response(
                {"detail": "El docente ya está deshabilitado."},
                status=status.HTTP_400_BAD_REQUEST
            )

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

        usuario_display = getattr(
            instance.usuario, "username", str(instance.usuario_id))
        return Response({"detail": f"Docente '{usuario_display}' deshabilitado correctamente."},
                        status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        '''
        Permite visualizar el detalle completo de un docente
        '''
        user = request.user

        self._ensure_manage_permission(user)

        instance = self.get_object()

        if not instance.activo:
            return Response(
                {"detail": "El docente está deshabilitado y no puede visualizarse."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = DocenteDetalleSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
