# Importaciones necesarias para esta vista
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from gestion_academica.serializers import RecuperarUsuarioSerializer

class RecuperarUsuarioView(views.APIView):
    """
    Endpoint para que un usuario recupere su nombre de usuario
    a través de su email.
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(request_body=RecuperarUsuarioSerializer)
    def post(self, request, *args, **kwargs):
        serializer = RecuperarUsuarioSerializer(data=request.data)
        
        if serializer.is_valid():
            usuario = serializer.validated_data['user']
            
            # Prepara y envía el email
            subject = "Recuperación de nombre de usuario - Mapa de Carreras"
            message = (
                f"Hola {usuario.first_name} {usuario.last_name}!\n\n"
                f"Recibimos una solicitud para recuperar tu nombre de usuario asociado a este correo electrónico. 🧠🔐\n\n"
                f"📛 Tu nombre de usuario es:\n\n"
                f"{usuario.username}\n\n"
                f"Si no solicitaste esta información, podés ignorar este mensaje. No se ha hecho ningún cambio en tu cuenta.\n\n"
                f"Gracias por usar nuestra app. \n\n"
                f"Saludos,\n"
                f"El equipo de Mapa de Carreras"
            )
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )
            
            return Response({"message": "Hemos enviado tu nombre de usuario a tu correo electrónico."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)