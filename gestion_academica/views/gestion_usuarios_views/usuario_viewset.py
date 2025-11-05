from rest_framework import viewsets, mixins
# Ahora el permiso por defecto debe ser más estricto
from rest_framework.permissions import IsAdminUser 
from gestion_academica.models.M4_gestion_usuarios_autenticacion import Usuario
from ...serializers.M4_gestion_usuarios_autenticacion import UsuarioSerializer
# importaciones para realizar el filtrado de usuarios deshabilitados
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..filters import UsuarioFilter
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
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):
    """ 
    ViewSet para la GESTIÓN DE USUARIOS (Solo Admin).
    NO se usa para registro público.
    Permite: Listar, Ver detalle, Actualizar y Borrar usuarios.
    """
    queryset = Usuario.objects.all().order_by('id')
    serializer_class = UsuarioSerializer
    
    # El permiso por defecto es ser Admin.
    permission_classes = [IsAdminUser]

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