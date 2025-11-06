
from django.http import Http404
from rest_framework import viewsets, mixins

# Permisos
from gestion_academica.permissions import EsAdministrador, EsCoordinadorDeCarrera, EsDocente, UsuarioViewSetPermission
# Modelos
from gestion_academica.models.M4_gestion_usuarios_autenticacion import Usuario, Coordinador
from gestion_academica.models.M2_gestion_docentes import Docente
# Serializers
from ...serializers import UsuarioSerializer, EditarDocenteSerializer, EditarCoordinadorSerializer, EditarUsuarioSerializer
# Importaciones para realizar el filtrado de usuarios deshabilitados
from rest_framework.filters import SearchFilter
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
        Devuelve un serializer diferente basado en el ROL del usuario.
        """
        usuario_que_pide = self.request.user

        # --- 1. LÓGICA DEL ADMINISTRADOR ---
        if EsAdministrador().has_permission(self.request, self):
            if self.action == 'list' or self.action == 'create':
                return UsuarioSerializer

            # Para 'retrieve' (GET), 'update' (PATCH), etc.
            try:
                pk = self.kwargs.get('pk')
                if not pk:
                    return UsuarioSerializer

                # Buscamos el usuario Y sus roles
                usuario_a_editar = Usuario.objects.prefetch_related(
                    'roles').get(pk=pk)

                if usuario_a_editar.roles.filter(nombre__iexact="DOCENTE").exists():
                    return EditarDocenteSerializer

                if usuario_a_editar.roles.filter(nombre__iexact="COORDINADOR").exists():
                    return EditarCoordinadorSerializer

                return UsuarioSerializer

            except Usuario.DoesNotExist:
                return UsuarioSerializer
            except Exception:
                return UsuarioSerializer

        # --- 2. LÓGICA DEL USUARIO NORMAL (NO ADMIN) ---
        if usuario_que_pide.roles.filter(nombre__iexact="COORDINADOR").exists():
            return EditarCoordinadorSerializer

        if usuario_que_pide.roles.filter(nombre__iexact="DOCENTE").exists():
            return EditarDocenteSerializer

        return EditarUsuarioSerializer

    def get_object(self):
        """
        Sobrescribe get_object para devolver la instancia del modelo
        hijo (Docente, Coordinador) si el serializer lo requiere,
        en lugar del modelo padre (Usuario).
        """
        pk = self.kwargs.get('pk')

        # Obtenemos la *clase* de serializer que se va a usar
        serializer_class = self.get_serializer_class()

        # 1. Si el serializer es el de Docente...
        if serializer_class == EditarDocenteSerializer:
            try:
                # ...buscamos y devolvemos el objeto Docente.
                return Docente.objects.get(pk=pk)  # Usa tu import de Docente
            except Docente.DoesNotExist:
                raise Http404("No se encontró el Docente.")

        # 2. Si el serializer es el de Coordinador...
        if serializer_class == EditarCoordinadorSerializer:
            try:
                # ...buscamos y devolvemos el objeto Coordinador.
                # Usa tu import de Coordinador
                return Coordinador.objects.get(pk=pk)
            except Coordinador.DoesNotExist:
                raise Http404("No se encontró el Coordinador.")

        # 3. Para cualquier otro caso (Admin, Alumno)...
        try:
            # ...devolvemos el objeto Usuario base.
            return Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist:
            raise Http404("No se encontró el Usuario.")

    @swagger_auto_schema(
        request_body=UsuarioSerializer
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Actualiza parcialmente (PATCH) un usuario.
        El serializer y los permisos se aplican dinámicamente
        según el rol del solicitante.
        """
        return super().partial_update(request, *args, **kwargs)
