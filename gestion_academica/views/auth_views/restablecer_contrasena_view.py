# Importaciones necesarias para esta vista
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from gestion_academica.serializers import RestablecerContraseñaSerializer
from gestion_academica.serializers.M4_gestion_usuarios_autenticacion import UsuarioSerializer

class RestablecerContraseñaView(views.APIView):
    """
    Endpoint para confirmar el reseteo de contraseña.
    Recibe email, código y la nueva contraseña.
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(request_body=RestablecerContraseñaSerializer)
    def post(self, request, *args, **kwargs):
        serializer = RestablecerContraseñaSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            password = serializer.validated_data['password']
            
            # Usamos una instancia de UsuarioSerializer solo para acceder
            # al método 'update_password_without_old'
            user_serializer = UsuarioSerializer()
            user_serializer.update_password_without_old(user, {'password': password})
            
            return Response({"message": "Tu contraseña ha sido actualizada con éxito."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)