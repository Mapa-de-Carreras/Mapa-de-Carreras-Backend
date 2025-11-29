from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from gestion_academica.serializers import PlanAsignaturaSerializer
from gestion_academica.permissions import EsAdministrador
from gestion_academica.services import plan_asignatura as plan_asignatura_service



class PlanAsignaturaListCreateView(APIView):
    
    def get_permissions(self):
        if self.request.method == "POST":
            return [EsAdministrador()]
        return [AllowAny()]

    @swagger_auto_schema(
        tags=["Gestión Académica - PlanAsignatura"],
        operation_summary="Listar PlanAsignatura",
        responses={200: PlanAsignaturaSerializer(many=True)},
        manual_parameters=[
            openapi.Parameter(
                'plan_id', 
                in_=openapi.IN_QUERY,  # Indica que es un query parameter
                type=openapi.TYPE_INTEGER, # Define el tipo de dato esperado
                description='ID del Plan de Estudio para filtrar las asignaturas asociadas.',
                required=False # Es un filtro opcional
            ),
        ]
    )
    def get(self, request):
        plan_id = request.query_params.get("plan_id")
        qs = plan_asignatura_service.listar_plan_asignaturas(plan_id)
        serializer = PlanAsignaturaSerializer(qs, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Gestión Académica - PlanAsignatura"],
        operation_summary="Crear PlanAsignatura",
        request_body=PlanAsignaturaSerializer,
        responses={201: PlanAsignaturaSerializer()}
    )
    def post(self, request):
        serializer = PlanAsignaturaSerializer(data=request.data)
        if serializer.is_valid():
            obj = plan_asignatura_service.crear_plan_asignatura(serializer.validated_data)
            return Response(PlanAsignaturaSerializer(obj).data, status=201)
        return Response(serializer.errors, status=400)
    
    
    
    
class PlanAsignaturaDetailView(APIView):
    
    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [EsAdministrador()]
        return [AllowAny()]

    @swagger_auto_schema(
        tags=["Gestión Académica - PlanAsignatura"],
        operation_summary="Obtener detalle de un PlanAsignatura",
        responses={200: PlanAsignaturaSerializer()}
    )
    def get(self, request, pk):
        obj = plan_asignatura_service.obtener_plan_asignatura(pk)
        return Response(PlanAsignaturaSerializer(obj).data)

    @swagger_auto_schema(
        tags=["Gestión Académica - PlanAsignatura"],
        operation_summary="Actualizar PlanAsignatura",
        request_body=PlanAsignaturaSerializer,
        responses={200: PlanAsignaturaSerializer()}
    )
    def put(self, request, pk):
        obj = plan_asignatura_service.obtener_plan_asignatura(pk)
        serializer = PlanAsignaturaSerializer(obj, data=request.data, partial=False)
        if serializer.is_valid():
            updated = plan_asignatura_service.actualizar_plan_asignatura(
                obj, serializer.validated_data
            )
            return Response(PlanAsignaturaSerializer(updated).data)
        return Response(serializer.errors, status=400)

    @swagger_auto_schema(
        tags=["Gestión Académica - PlanAsignatura"],
        operation_summary="Eliminar PlanAsignatura",
        responses={204: "Eliminado"}
    )
    def delete(self, request, pk):
        obj = plan_asignatura_service.obtener_plan_asignatura(pk)
        plan_asignatura_service.eliminar_plan_asignatura(obj)
        return Response(status=204)

