# gestion_academica/views/auth_views/autenticacion_view.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from gestion_academica.serializers.M4_gestion_usuarios_autenticacion import LoginSerializer, LogoutSerializer
from gestion_academica.serializers.user_serializers.leer_usuario_serializer import LeerUsuarioSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny


class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: openapi.Response("Login exitoso", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                'access': openapi.Schema(type=openapi.TYPE_STRING),

                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'legajo': openapi.Schema(type=openapi.TYPE_STRING),
                'fecha_nacimiento': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'celular': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                'roles': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                'docente_data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                'coordinador_data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),


            }
        ))}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.validated_data['user']
            refresh = RefreshToken.for_user(usuario)

            user_serializer = LeerUsuarioSerializer(
                usuario, context={'request': request})
            user_data = user_serializer.data

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'usuario': user_data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    @swagger_auto_schema(
        request_body=LogoutSerializer,
        responses={200: "Sesión cerrada correctamente"}
    )
    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)

        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data['refresh_token']
                token = RefreshToken(refresh_token)
                token.blacklist()  # Invalida el token
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                return Response({"error": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
