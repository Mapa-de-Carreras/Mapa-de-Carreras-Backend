# gestion_academica/views/gestion_academica_views/planes.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from gestion_academica.serializers import PlanDeEstudioSerializerList,PlanDeEstudioSerializerDetail,PlanDeEstudioCreateUpdateSerializer,PlanDeEstudioVigenciaSerializer,PlanAsignaturaSerializer,CorrelativaCreateSerializer,CorrelativaSerializer
from gestion_academica.services import plan_de_estudio
from gestion_academica.permissions import EsAdministrador


class PlanDeEstudioListCreateView(APIView):
    """Listar o crear Planes de Estudio"""

    def get_permissions(self):
        if self.request.method == "POST":
            return [EsAdministrador]
        return [AllowAny()]

    @swagger_auto_schema(
        tags=["Gestión Académica - Planes de Estudio"],
        operation_summary="Listar Planes de Estudio",
        operation_description="Obtiene la lista completa de planes registrados.",
        responses={200: PlanDeEstudioSerializerList(many=True)}
    )
    def get(self, request):
        planes = plan_de_estudio.listar_planes()
        serializer = PlanDeEstudioSerializerList(planes, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=PlanDeEstudioCreateUpdateSerializer,
        responses={201: PlanDeEstudioSerializerList()},
        operation_description="Permite que un administrador o Coordinador de la carrera cree un nuevo plan de estudio ",
        tags=["Gestión Académica - Planes de Estudio"]
    )
    def post(self, request):
        serializer = PlanDeEstudioCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            plan = plan_de_estudio.crear_plan(serializer.validated_data, request.user)
            return Response({
                "message": "Plan de estudio creado correctamente.",
                "data": PlanDeEstudioSerializerList(plan).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "Error al crear el plan de estudio.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PlanDeEstudioDetailView(APIView):
    """Obtener, actualizar o eliminar un Plan de Estudio"""

    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [EsAdministrador]
        return [AllowAny()]

    @swagger_auto_schema(
        tags=["Gestión Académica - Planes de Estudio"],
        operation_summary="Obtener Plan de Estudio",
        operation_description="Permite ver el detalle de un plan de estudio.",
        responses={200: PlanDeEstudioSerializerDetail()}
    )
    def get(self, request, pk):
        plan = plan_de_estudio.obtener_plan(pk)
        serializer = PlanDeEstudioSerializerDetail(plan)
        return Response(serializer.data,status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=PlanDeEstudioCreateUpdateSerializer,
        tags=["Gestión Académica - Planes de Estudio"],
        operation_description="Permite que un administrador o coordinador de la carrera edite un plan de estudio.",
    )
    def put(self, request, pk):
        plan = plan_de_estudio.obtener_plan(pk)
        serializer = PlanDeEstudioCreateUpdateSerializer(instance=plan,data=request.data)
        if serializer.is_valid():
            plan = plan_de_estudio.actualizar_plan(pk, serializer.validated_data)
            return Response({
                "message": "Plan de estudio actualizado correctamente.",
                "data": PlanDeEstudioSerializerList(plan).data
            })
        return Response({
            "message": "Error al actualizar el plan de estudio.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["Gestión Académica - Planes de Estudio"],
        operation_summary="Eliminar un Plan de Estudio",
        operation_description="Permite que un administrador o coordinador de la carrera elimine un plan de estudio.",
        responses={200: "Plan eliminado correctamente"}
    )
    def delete(self, request, pk):
        plan_de_estudio.eliminar_plan(pk)
        return Response({
            "message": "Plan de estudio eliminado correctamente."
        }, status=status.HTTP_200_OK)
        

class PlanDeEstudioVigenciaView(APIView):
    """Cambiar la vigencia de un Plan de Estudio"""

    def get_permissions(self):
        return [EsAdministrador]

    @swagger_auto_schema(
        tags=["Gestión Académica - Planes de Estudio"],
        operation_summary="Cambiar vigencia de un Plan de Estudio",
        operation_description=(
            "Permite activar o desactivar la vigencia de un plan de estudio. "
            "Solo accesible para administradores o coordinadores de la carrera correspondiente."
        ),
        request_body=PlanDeEstudioVigenciaSerializer,
        responses={
            200: "Vigencia actualizada correctamente.",
            400: "Error en los datos enviados.",
            403: "No tiene permisos para modificar este plan.",
            404: "Plan de estudio no encontrado."
        }
    )
    def patch(self, request, pk):
        plan = plan_de_estudio.obtener_plan(pk)
        serializer = PlanDeEstudioVigenciaSerializer(plan, data=request.data, partial=True)

        if serializer.is_valid():
            plan_actualizado = plan_de_estudio.cambiar_vigencia(pk, serializer.validated_data["esta_vigente"])
            return Response({
                "message": "Vigencia del plan actualizada correctamente.",
                "data": PlanDeEstudioSerializerList(plan_actualizado).data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Error al actualizar la vigencia del plan de estudio.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
             

class ListarCorrelativasDeAsignaturaView(APIView):
    """Lista todas las correlativas de una asignatura dentro de un plan."""
    permission_classes = [EsAdministrador]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'plan_asignatura_id',
                openapi.IN_QUERY,
                description="ID de la asignatura dentro del plan (PlanAsignatura)",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        tags=["Gestión Académica - Planes de Estudio"],
        operation_summary="Listar correlativas de una asignatura",
        operation_description="Devuelve todas las correlativas asociadas a una asignatura dentro de un plan de estudio.",
        responses={200: CorrelativaSerializer(many=True)}
    )
    def get(self, request):
        plan_asignatura_id = request.query_params.get("plan_asignatura_id")

        if not plan_asignatura_id:
            return Response({
                "message": "Debe especificar el parámetro 'plan_asignatura_id'."
            }, status=status.HTTP_400_BAD_REQUEST)

        correlativas = plan_de_estudio.listar_correlativas_por_asignatura(plan_asignatura_id)
        serializer = CorrelativaSerializer(correlativas, many=True)
        return Response( serializer.data, status=status.HTTP_200_OK)



class AsignarCorrelativaView(APIView):
    """
    Asigna una correlativa a una asignatura dentro de un mismo plan de estudio.
    """

    permission_classes = [EsAdministrador]  # luego se puede cambiar por EsAdministrador | EsCoordinadorDeCarrera

    @swagger_auto_schema(
        request_body=CorrelativaCreateSerializer,
        tags=["Gestión Académica - Planes de Estudio"],
        operation_summary="Asignar correlativa a una asignatura",
        operation_description=(
            "Permite asignar una correlativa a una asignatura de un plan de estudio. "
            "Las correlativas deben pertenecer al mismo plan y cumplir las reglas de correlatividad."
        ),
        responses={
            201: "Correlativa asignada correctamente.",
            400: "Error de validación o correlativa duplicada."
        },
    )
    def post(self, request):
        serializer = CorrelativaCreateSerializer(data=request.data)
        if serializer.is_valid():
            correlativa =plan_de_estudio.crear_correlativa(serializer.validated_data)
            return Response({
                "message": "Correlativa asignada correctamente.",
                "data": CorrelativaCreateSerializer(correlativa).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "message": "Error al asignar la correlativa.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    
class EliminarCorrelativaView(APIView):
    """
    Elimina una correlativa específica del plan de estudio.
    """

    permission_classes = [EsAdministrador]

    @swagger_auto_schema(
        tags=["Gestión Académica - Planes de Estudio"],
        operation_summary="Eliminar correlativa de una asignatura",
        operation_description="Permite eliminar una correlativa asociada a una asignatura del plan de estudio.",
        responses={
            200: "Correlativa eliminada correctamente.",
            404: "Correlativa no encontrada."
        }
    )
    def delete(self, request, pk):
        plan_de_estudio.eliminar_correlativa(pk)
        return Response({
            "message": "Correlativa eliminada correctamente."
        }, status=status.HTTP_200_OK)