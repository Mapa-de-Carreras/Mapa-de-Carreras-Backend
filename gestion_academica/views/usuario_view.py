from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from gestion_academica.models.M4_gestion_usuarios_autenticacion import Usuario
from ..serializers.M4_gestion_usuarios_autenticacion import UsuarioSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    """ ViewSet para crear (registrar), ver, actualizar y eliminar usuarios """
    queryset = Usuario.objects.all().order_by('id')
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        """ Asigna permisos basados en la acción """
        if self.action == 'create':
            # Cualquiera puede registrarse
            permission_classes = [AllowAny]
        else:
            # Para 'list', 'retrieve', 'update', 'partial_update', 'destroy'
            # debe estar autenticado --- Se puede adaptar a ADMIN más adelante según casos de uso
            permission_classes = [IsAuthenticated]             
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """ Sobrescribimos 'create' para que use el serializer """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # Nota: No se devuelven tokens JWT aquí.
        # El registro solo crea la cuenta. El usuario debe
        # ir a /api/auth/login/ por separado para obtener sus tokens.
        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)