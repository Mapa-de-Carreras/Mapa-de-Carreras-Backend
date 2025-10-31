from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from gestion_academica.serializers.M1_gestion_academica import AsignaturaSerializer
from gestion_academica.services import asignaturas as asignatura_service

class AsignaturaListCreateView(APIView):
    """Listar o crear Asignaturas"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]

    # --- Parámetro de filtro para Swagger ---
    filtro_activas = openapi.Parameter(
        "activas",
        openapi.IN_QUERY,
        description="Filtra las asignaturas por estado. Usa 'true' o 'false'.",
        type=openapi.TYPE_BOOLEAN
    )

    @swagger_auto_schema(
        tags=["Gestión Académica - Asignaturas"],
        operation_summary="Listar Asignaturas",
        operation_description="Devuelve el listado completo de asignaturas registradas. Se puede filtrar por estado activo.",
        manual_parameters=[filtro_activas],
        responses={200: AsignaturaSerializer(many=True)}
    )
    def get(self, request):
        activas_param = request.query_params.get("activas")
        activas = None
        if activas_param is not None:
            activas = activas_param.lower() in ["true", "1", "t", "yes"]

        asignaturas = asignatura_service.listar_asignaturas(activas)
        serializer = AsignaturaSerializer(asignaturas, many=True)

        msg = "Listado de asignaturas obtenido correctamente."
        if activas is not None:
            msg = f"Listado de asignaturas {'activas' if activas else 'inactivas'}."

        return Response({
            "message": msg,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["Gestión Académica - Asignaturas"],
        security=[{"Bearer": []}],
        operation_summary="Crear una nueva Asignatura",
        operation_description="Permite al administrador registrar una nueva asignatura.",
        request_body=AsignaturaSerializer,
        responses={
            201: openapi.Response("Asignatura creada correctamente", AsignaturaSerializer),
            400: "Error en los datos enviados"
        }
    )
    def post(self, request):
        serializer = AsignaturaSerializer(data=request.data)
        if serializer.is_valid():
            asignatura = asignatura_service.crear_asignatura(serializer.validated_data)
            return Response({
                "message": "Asignatura creada correctamente.",
                "data": AsignaturaSerializer(asignatura).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "Error al crear la asignatura.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        
        
class AsignaturaDetailView(APIView):
    """Obtener, actualizar o eliminar una Asignatura"""

    def get_permissions(self):
        if self.request.method in ["PUT", "DELETE"]:
            return [IsAdminUser()]
        return [AllowAny()]

    @swagger_auto_schema(
        tags=["Gestión Académica - Asignaturas"],
        operation_summary="Obtener detalle de una Asignatura",
        operation_description="Devuelve la información completa de una asignatura específica.",
        responses={200: AsignaturaSerializer()}
    )
    def get(self, request, pk):
        asignatura = asignatura_service.obtener_asignatura(pk)
        serializer = AsignaturaSerializer(asignatura)
        return Response({
            "message": f"Asignatura '{serializer.data.get('nombre')}' obtenida correctamente.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["Gestión Académica - Asignaturas"],
        security=[{"Bearer": []}],
        operation_summary="Actualizar una Asignatura",
        operation_description="Permite al administrador modificar los datos de una asignatura.",
        request_body=AsignaturaSerializer,
        responses={
            200: openapi.Response("Asignatura actualizada correctamente", AsignaturaSerializer),
            400: "Error en los datos enviados"
        }
    )
    def put(self, request, pk):
        asignatura = asignatura_service.obtener_asignatura(pk)
        serializer = AsignaturaSerializer(asignatura, data=request.data, partial=True)
        if serializer.is_valid():
            asignatura_actualizada = asignatura_service.actualizar_asignatura(pk, serializer.validated_data)
            return Response({
                "message": "Asignatura actualizada correctamente.",
                "data": AsignaturaSerializer(asignatura_actualizada).data
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "Error al actualizar la asignatura.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Gestión Académica - Asignaturas"],
        security=[{"Bearer": []}],
        operation_summary="Eliminar una Asignatura",
        operation_description="Permite al administrador desactivar (borrado lógico) una asignatura.",
        responses={200: "Asignatura desactivada correctamente"}
    )
    def delete(self, request, pk):
        asignatura = asignatura_service.eliminar_asignatura(pk)
        return Response({
            "message": f"La asignatura '{asignatura.nombre}' fue desactivada correctamente."
        }, status=status.HTTP_200_OK)