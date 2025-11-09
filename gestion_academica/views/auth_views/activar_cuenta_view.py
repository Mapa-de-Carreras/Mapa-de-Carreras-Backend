# gestion_academica/views/auth_views/activar_cuenta_view.py

from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from gestion_academica.serializers.auth_serializers.activar_cuenta_serializer import ActivarCuentaSerializer
from drf_yasg.utils import swagger_auto_schema


class ActivarCuentaView(views.APIView):
    """
    Endpoint para activar una cuenta de usuario nueva
    usando el código enviado por email.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=ActivarCuentaSerializer)
    def post(self, request, *args, **kwargs):
        serializer = ActivarCuentaSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Activamos el usuario
            user.is_active = True
            user.save()

            return Response({"message": "Tu cuenta ha sido activada con éxito."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
