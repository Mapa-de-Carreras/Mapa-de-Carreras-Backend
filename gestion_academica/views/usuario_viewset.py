from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
# Ahora el permiso por defecto debe ser más estricto
from rest_framework.permissions import IsAdminUser 

from gestion_academica.models.M4_gestion_usuarios_autenticacion import Usuario
from ..serializers.M4_gestion_usuarios_autenticacion import UsuarioSerializer

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