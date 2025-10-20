from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers.gestion_usuario_serializer.login_serializer import LoginSerializer, LogoutSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class LoginView(APIView):
    # --- AÑADE ESTE DECORADOR ---
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: openapi.Response("Login exitoso", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                'access': openapi.Schema(type=openapi.TYPE_STRING),
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            }
        ))}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.validated_data['user']
            refresh = RefreshToken.for_user(usuario)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'id': usuario.id,
                'is_staff': usuario.is_staff,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    # --- AÑADE ESTE DECORADOR ---
    @swagger_auto_schema(
        request_body=LogoutSerializer,
        responses={200: "Sesión cerrada correctamente"}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response({"detail": "Refresh token no proporcionado"}, status=status.HTTP_400_BAD_REQUEST)
            # Intenta agregar el token a la lista negra
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)