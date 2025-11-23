from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from gestion_academica.serializers.M3_designaciones_docentes import (
    ComisionSerializer,
    ComisionCreateUpdateSerializer
)
from gestion_academica.services.designaciones_docentes import gestion_comision


class ComisionListCreateView(APIView):
    """
    Listar o Crear Comisiones
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["Gestión Académica - Comisiones"],
        operation_summary="Listar Comisiones",
        operation_description="Devuelve todas las comisiones registradas del sistema.",
        responses={200: ComisionSerializer(many=True)}
    )
    def get(self, request):
        comisiones = gestion_comision.listar_comisiones()
        serializer = ComisionSerializer(comisiones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=ComisionCreateUpdateSerializer,
        tags=["Gestión Académica - Comisiones"],
        operation_summary="Crear una Comisión",
        operation_description="Crea una nueva comisión para una asignatura.",
    )
    def post(self, request):
        serializer = ComisionCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            gestion_comision.crear_comision(serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response({
            "message": "Error al crear la comisión.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ComisionDetailView(APIView):
    """
    Obtener, Actualizar o Eliminar una Comisión
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["Gestión Académica - Comisiones"],
        operation_summary="Obtener detalle de una Comisión",
        operation_description="Devuelve la información detallada de una comisión.",
        responses={200: ComisionSerializer()}
    )
    def get(self, request, pk):
        comision = gestion_comision.obtener_comision(pk)
        serializer = ComisionSerializer(comision)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=ComisionCreateUpdateSerializer,
        tags=["Gestión Académica - Comisiones"],
        operation_summary="Actualizar Comisión",
        operation_description="Permite editar una comisión existente (nombre, turno, promoción, etc.)."
    )
    def put(self, request, pk):
        serializer = ComisionCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            comision = gestion_comision.actualizar_comision(pk, serializer.validated_data)
            return Response({
                "message": "Comisión actualizada correctamente.",
                "data": ComisionSerializer(comision).data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Error al actualizar la comisión.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Gestión Académica - Comisiones"],
        operation_summary="Eliminar Comisión",
        operation_description="Elimina una comisión del sistema.",
        responses={200: "Comisión eliminada correctamente."}
    )
    def delete(self, request, pk):
        gestion_comision.eliminar_comision(pk)
        return Response({
            "message": "Comisión eliminada correctamente."
        }, status=status.HTTP_200_OK)
