from rest_framework import generics
from ..permissions import IsCoordinadorOrDocente
from rest_framework.permissions import IsAuthenticated
from gestion_academica.models import Usuario
from ..serializers.user_serializers import EditarUsuarioSerializer

class EditarUsuarioView(generics.RetrieveUpdateAPIView):
    """
    Endpoint para que un usuario vea (GET) y actualice (PATCH)
    su propio perfil.
    - GET: Permite a cualquier usuario autenticado ver su perfil.
    - PATCH: Permite solo a Coordinador/Docente editar su perfil.
    """
    queryset = Usuario.objects.all()
    serializer_class = EditarUsuarioSerializer

    def get_permissions(self):
        """
        Asigna permisos basados en el método de la petición.
        """
        if self.request.method == 'GET':
            # Para 'ver' (GET), solo necesita estar logueado
            return [IsAuthenticated()]
        
        # Para 'editar' (PATCH, PUT), necesita ser Coordinador o Docente
        return [IsCoordinadorOrDocente()]

    def get_object(self):
        """
        Sobrescribimos esto para que SIEMPRE devuelva el usuario
        autenticado (request.user).
        
        Esto es lo que impide que un usuario edite a otro.
        """
        return self.request.user