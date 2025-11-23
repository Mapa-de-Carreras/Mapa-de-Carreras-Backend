
from django.http import Http404
from rest_framework import viewsets, mixins

# Permisos
from gestion_academica.permissions import EsAdministrador, UsuarioViewSetPermission
# Modelos
from gestion_academica.models.M4_gestion_usuarios_autenticacion import Usuario
# Serializers
# from ...serializers import (
#     UsuarioSerializer,
#     EditarUsuarioSerializer,
#     AdminUsuarioDetalleSerializer
# )
from ...serializers.user_serializers.usuario_serializer import UsuarioSerializer, AdminUsuarioDetalleSerializer
from ...serializers.user_serializers.leer_usuario_serializer import LeerUsuarioSerializer
from ...serializers.user_serializers.editar_usuario_serializer import EditarUsuarioSerializer
# Importaciones para realizar el filtrado de usuarios deshabilitados
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .filters import UsuarioFilter
# Swagger
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

user_list_params = [
    openapi.Parameter(
        'is_active',
        openapi.IN_QUERY,
        description="Filtrar por estado (true/false)",
        type=openapi.TYPE_BOOLEAN
    ),
    openapi.Parameter(
        'username',
        openapi.IN_QUERY,
        description="Filtrar por nombre de usuario exacto (ignora mayúsculas)",
        type=openapi.TYPE_STRING
    ),
    openapi.Parameter(
        'email',
        openapi.IN_QUERY,
        description="Filtrar por email exacto (ignora mayúsculas)",
        type=openapi.TYPE_STRING
    )
]
# Heredamos de GenericViewSet y los mixins que SÍ queremos.
# (Listar, Ver, Actualizar, Borrar).
# OMITIMOS 'mixins.CreateModelMixin' porque el create lo
# maneja la view de registrar_usuario


class UsuarioViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """ 
    ViewSet para la GESTIÓN DE USUARIOS (Datos base).

    Permite:
    - Admin: Listar, Ver, Actualizar (todo), Borrar.
    - Usuarios: Ver y Actualizar (solo sus datos personales).

    PARA GESTIONAR DATOS DE ROL (ej: modalidad de docente
    o carreras de coordinador) USE LOS ENDPOINTS:
    - /api/docentes/{pk}/
    - /api/coordinadores/{pk}/
    """
    queryset = Usuario.objects.all().order_by('id')
    serializer_class = UsuarioSerializer

    # El permiso por defecto es ser Admin.
    permission_classes = [UsuarioViewSetPermission]

    ''' Lógica para filtrado de usuarios deshabilitados '''
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # (Paso 1) Permite filtrar por estado (y otros campos)
    filterset_class = UsuarioFilter
    # (Paso 1) Permite buscar por nombre y apellido
    search_fields = ['first_name', 'last_name', 'username']

    # --- SOBREESCRIBE EL MÉTODO 'list' PARA DECORARLO ---
    @swagger_auto_schema(manual_parameters=user_list_params)
    def list(self, request, *args, **kwargs):
        """ Lista, filtra (manualmente decorado para Swagger) y busca usuarios """
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        """
        Devuelve un serializer diferente basado en la ACCIÓN
        y el ROL del *solicitante*.
        """
        # 1. Comprobar quién está haciendo la solicitud
        es_admin = EsAdministrador().has_permission(self.request, self)

        # 2. Comprobar la acción
        action = self.action

        # 3. Lógica de decisión
        if action in ['list', 'retrieve']:
            # Para GET (Detalle), usamos el serializer más rico que
            # muestra los perfiles anidados de Docente y Coordinador.
            # UsuarioViewSetPermission ya restringe *quién* se puede ver.
            # return AdminUsuarioDetalleSerializer

            # NUEVO: ahora usamos LeerUsuarioSerializer para evitar mostrar password/is_staff y para devoler roles como objetos
            return LeerUsuarioSerializer

        if action in ['update', 'partial_update']:
            if es_admin:
                # El Admin usa el serializer que PUEDE cambiar roles
                # (y que tiene la lógica de desactivar carreras)
                return UsuarioSerializer
            else:
                # Un usuario normal solo puede editar sus datos personales
                return EditarUsuarioSerializer

        # Para 'list', 'create', o cualquier otra, usa el default
        return UsuarioSerializer

    # NUEVO
    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [UsuarioViewSetPermission()]

    def get_object(self):
        """
        Sobrescribe get_object para devolver SIEMPRE
        la instancia base de Usuario.
        """
        pk = self.kwargs.get('pk')
        try:
            # Siempre busca y devuelve el objeto Usuario base
            return Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            raise Http404("No se encontró el Usuario.")

    @swagger_auto_schema(
        request_body=UsuarioSerializer
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Actualiza parcialmente (PATCH) un usuario.
        El serializer se aplica dinámicamente:
        - Admin: Usa UsuarioSerializer (puede cambiar roles).
        - Usuario normal: Usa EditarUsuarioSerializer (solo datos personales).
        """
        return super().partial_update(request, *args, **kwargs)
