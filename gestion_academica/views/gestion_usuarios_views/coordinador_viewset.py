from django.http import Http404
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from django.db import transaction

# Modelos
from gestion_academica.models import Coordinador, Usuario, Rol, RolUsuario
# Serializers
from gestion_academica.serializers.user_serializers import EditarCoordinadorSerializer, CoordinadorSerializer, UsuarioSerializer
# Permisos
from gestion_academica.permissions import EsAdministrador, EsCoordinadorDeCarrera

class CoordinadorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la GESTIÓN DE COORDINADORES.
    Permite: Listar, Ver detalle, Crear, Actualizar y Borrar Coordinadores.
    """
    queryset = Coordinador.objects.all().order_by('id')
    serializer_class = CoordinadorSerializer
    lookup_field = 'usuario__id'

    def get_permissions(self):
        """
        Un Coordinador puede editar (PATCH) o ver (GET) su propio
        perfil, pero solo un Admin puede Listar, Crear o Borrar.
        """
        if self.action in ['retrieve', 'update', 'partial_update']:
            # Permite a un Coordinador ver/editar su perfil, O a un Admin
            return [(EsAdministrador | EsCoordinadorDeCarrera)()]
        
        # Para list, create, destroy, solo Admin
        return [EsAdministrador()]

    def get_serializer_class(self):
        """
        Usa el serializer de edición para las acciones de 
        actualización (PATCH/PUT).
        """
        if self.action in ['update', 'partial_update']:
            return EditarCoordinadorSerializer
        
        # Para create, list, retrieve
        return CoordinadorSerializer

    def create(self, request, *args, **kwargs):
        """
        Lógica para crear un Coordinador (que también es un Usuario).
        Esto asume que los datos del usuario (username, password, etc.)
        vienen en el request.
        """
        
        # Usaremos el UsuarioSerializer para crear el objeto base
        # pero con el modelo Coordinador
        user_serializer = UsuarioSerializer(data=request.data, context=self.get_serializer_context())
        user_serializer.Meta.model = Coordinador
        
        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # El .create() del UsuarioSerializer se encarga de todo
                # (password, campos base, etc.)
                coordinador = user_serializer.save()
                
                # Aseguramos el rol
                rol_coord, _ = Rol.objects.get_or_create(nombre__iexact="COORDINADOR")
                RolUsuario.objects.get_or_create(usuario=coordinador, rol=rol_coord)
                
                # Si es Admin, también le damos ese rol
                if coordinador.is_staff or coordinador.is_superuser:
                    rol_admin, _ = Rol.objects.get_or_create(nombre__iexact="ADMINISTRADOR")
                    RolUsuario.objects.get_or_create(usuario=coordinador, rol=rol_admin)
            
        except Exception as e:
            return Response({"detail": f"Error al crear coordinador: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Devolvemos la data usando el serializer de Coordinador
        out_serializer = CoordinadorSerializer(coordinador, context=self.get_serializer_context())
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)