from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from gestion_academica.serializers.M1_gestion_academica import InstitutoSerializer
from rest_framework.permissions import AllowAny
from gestion_academica.permissions import EsAdministrador, EsCoordinadorDeCarrera
from gestion_academica.services.gestion_academica import institutos as instituto_service
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class InstitutoListCreateView(APIView):
    """Listar o crear Institutos"""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsAdministrador()]
        return [AllowAny()]

    # ------------------------------
    # GET - Listar Institutos
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Institutos"],
        operation_summary="Listar todos los Institutos",
        operation_description="Devuelve un listado completo de los institutos registrados en el sistema. Acceso público.",
        responses={200: InstitutoSerializer(many=True)}
    )
    def get(self, request):
        institutos = instituto_service.listar_institutos()
        serializer = InstitutoSerializer(institutos, many=True)
        return Response({
            "message": "Listado de institutos obtenido correctamente.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ------------------------------
    # POST - Crear Instituto
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Institutos"],
        operation_summary="Crear un nuevo Instituto",
        operation_description="Permite al administrador registrar un nuevo instituto en el sistema.",
        request_body=InstitutoSerializer,
        responses={
            201: openapi.Response("Instituto creado correctamente", InstitutoSerializer),
            400: "Error en los datos enviados"
        }
    )
    def post(self, request):
        datos = request.data.copy()
    
        serializer = InstitutoSerializer(data=datos)
        if serializer.is_valid():
            instituto = instituto_service.crear_instituto(serializer.validated_data)
            return Response({
                "message": "Instituto creado correctamente.",
                "data": InstitutoSerializer(instituto).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "Error al crear el instituto.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



class InstitutoDetailView(APIView):
    """Obtener, actualizar o eliminar un Instituto"""

    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [EsAdministrador()]
        return [AllowAny()]

    # ------------------------------
    # GET - Detalle
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Institutos"],
        operation_summary="Obtener detalle de un Instituto",
        operation_description="Devuelve la información completa de un instituto específico. Acceso público.",
        responses={200: InstitutoSerializer()}
    )
    def get(self, request, pk):
        instituto = instituto_service.obtener_instituto(pk)
        serializer = InstitutoSerializer(instituto)
        return Response({
            "message": f"Instituto '{serializer.data.get('nombre')}' obtenido correctamente.",
            "data": serializer.data
        })

    # ------------------------------
    # PUT - Actualizar
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Institutos"],
        operation_summary="Actualizar un Instituto",
        operation_description="Permite al administrador modificar los datos de un instituto existente.",
        request_body=InstitutoSerializer,
        responses={
            200: openapi.Response("Instituto actualizado correctamente", InstitutoSerializer),
            400: "Error en los datos enviados"
        }
    )
    def put(self, request, pk):
        instituto = instituto_service.obtener_instituto(pk)
        serializer = InstitutoSerializer(instituto, data=request.data, partial=True)
        if serializer.is_valid():
            instituto_actualizado = instituto_service.actualizar_instituto(pk, serializer.validated_data)
            return Response({
                "message": "Instituto actualizado correctamente.",
                "data": InstitutoSerializer(instituto_actualizado).data
            })
        return Response({
            "message": "Error al actualizar el instituto.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------
    # DELETE - Eliminar
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Institutos"],
        operation_summary="Eliminar un Instituto",
        operation_description="Permite al administrador eliminar un instituto del sistema.",
        responses={200: "Instituto eliminado correctamente"}
    )
    def delete(self, request, pk):
        instituto_service.eliminar_instituto(pk)
        return Response({
            "message": "Instituto eliminado correctamente."
        }, status=status.HTTP_200_OK)


