from rest_framework import generics, status
from rest_framework.response import Response
from ..serializers.auth_serializers import CambiarContrasenaSerializer
from rest_framework.permissions import IsAuthenticated
from gestion_academica.models import Usuario

class CambiarContrasenaView(generics.UpdateAPIView):
    """
    Endpoint para que un usuario logueado cambie su contraseña.
    """
    serializer_class = CambiarContrasenaSerializer
    permission_classes = [IsAuthenticated]
    queryset = Usuario.objects.all()

    def get_object(self):
        # El objeto a actualizar es siempre el usuario logueado
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Sobrescribimos 'update' para dar un mensaje de éxito
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # El serializer.update() se encarga de guardar
            serializer.update(user, serializer.validated_data)
            return Response({"message": "Contraseña actualizada con éxito."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)