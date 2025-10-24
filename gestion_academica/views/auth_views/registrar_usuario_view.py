
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema

from gestion_academica.serializers.M4_gestion_usuarios_autenticacion import UsuarioSerializer
from gestion_academica.serializers import EnviarCodigoVerificacionSerializer 

class UsuarioRegistroView(views.APIView):
    """
    Vista para registrar un nuevo usuario.
    Crea el usuario como 'inactivo' y automáticamente 
    envía un código de activación a su email.
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(request_body=UsuarioSerializer)
    def post(self, request, *args, **kwargs):
        
        # 1. Intentar crear el usuario
        user_serializer = UsuarioSerializer(data=request.data)
        if user_serializer.is_valid():
            # .save() llama al método .create()
            # El usuario se guarda con is_active=False
            user = user_serializer.save() 
            
            # 2. Si se crea, preparar y enviar el código de activación
            code_serializer_data = {
                "email": user.email, # Usamos el email del usuario recién creado
                "contexto": "registro"
            }
            code_serializer = EnviarCodigoVerificacionSerializer(data=code_serializer_data)
            
            if code_serializer.is_valid():
                try:
                    # .enviar_codigo() envía el email
                    code_serializer.enviar_codigo() 
                    
                    # Devolvemos los datos del usuario creado (sin contraseña)
                    response_data = user_serializer.data 
                    
                    return Response(response_data, status=status.HTTP_201_CREATED)
                
                except Exception as e:
                    # Si falla el envío de email, borramos el usuario creado
                    # para que pueda intentarlo de nuevo (Rollback)
                    user.delete()
                    return Response({
                        "error": "No se pudo enviar el email de verificación. Intente de nuevo.",
                        "detail": str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            else:
                # Si falla la validación del code_serializer
                user.delete() # Rollback
                return Response(code_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Si la validación del usuario falla (ej: email duplicado, contraseña débil)
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)