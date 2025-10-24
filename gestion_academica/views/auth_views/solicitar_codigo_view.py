# En tu archivo de vistas (ej: views/auth/password_views.py)

from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema

from django.contrib.auth import get_user_model

#serializer que envia el codigo.
#alias = Source 1
from gestion_academica.serializers.auth_serializers.enviar_codigo_verificacion_serializer import EnviarCodigoVerificacionSerializer
#serializer que valida que se reciba un email desde la app
from gestion_academica.serializers.auth_serializers import EmailSerializer

User = get_user_model()

class SolicitarCodigoView(views.APIView):
    """
    Vista "inteligente" para que la app solicite un código.
    Recibe solo un email y el backend decide qué hacer.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=EmailSerializer)
    def post(self, request, *args, **kwargs):
        
        # 1. Validar que nos enviaron un email
        email_serializer = EmailSerializer(data=request.data)
        if not email_serializer.is_valid():
            return Response(email_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = email_serializer.validated_data['email']

        # 2. Lógica "inteligente": Buscar al usuario
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Este correo no está registrado."}, status=status.HTTP_400_BAD_REQUEST)
        
        # 3. Decidir el contexto
        if user.is_active:
            contexto = "recuperacion"
        else:
            contexto = "reenviar_activacion"
            
        # 4. Preparar los datos para el serializer "tonto" (Source 1)
        data_para_enviar = {
            "email": email,
            "contexto": contexto
        }
        
        # 5. Llamar al serializer (Source 1) para que haga el trabajo
        code_serializer = EnviarCodigoVerificacionSerializer(data=data_para_enviar)
        
        # Validamos (esto correrá la lógica de validate de Source 1)
        if code_serializer.is_valid():
            code_serializer.enviar_codigo()
            return Response({"message": "Se ha enviado un código a tu correo."}, status=status.HTTP_200_OK)
        else:
            # Si falla, devuelve el error (ej: "cuenta ya activa")
            return Response(code_serializer.errors, status=status.HTTP_400_BAD_REQUEST)