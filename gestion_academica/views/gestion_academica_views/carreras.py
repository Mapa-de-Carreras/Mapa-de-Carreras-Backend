from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from gestion_academica.permissions import EsAdministrador, EsCoordinadorDeCarrera
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from gestion_academica.serializers.M1_gestion_academica import CarreraSerializer,CarreraCreateUpdateSerializer,CarreraVigenciaUpdateSerializer
from gestion_academica.services.gestion_academica import carreras as carrera_service



class CarreraListCreateView(APIView):
    """Listar o crear Carreras"""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EsAdministrador()]
        return [AllowAny()]

    # Definimos los parámetros de filtro para Swagger
    filtro_vigentes = openapi.Parameter(
        'vigentes',
        openapi.IN_QUERY,
        description="Filtra las carreras por vigencia. Usa 'true' o 'false'.",
        type=openapi.TYPE_BOOLEAN
    )

    filtro_instituto = openapi.Parameter(
        'instituto_id',
        openapi.IN_QUERY,
        description="Filtra las carreras pertenecientes a un instituto específico (por ID).",
        type=openapi.TYPE_INTEGER
    )

    @swagger_auto_schema(
        tags=["Gestión Académica - Carreras"],
        operation_summary="Listar todas las Carreras",
        operation_description=(
            "Devuelve el listado completo de carreras registradas. "
            "Se puede filtrar opcionalmente por vigencia o por ID de instituto."
        ),
        manual_parameters=[filtro_vigentes, filtro_instituto],
        responses={200: CarreraSerializer(many=True)}
    )
    def get(self, request):
        # Obtenemos los parámetros de query
        vigentes_param = request.query_params.get('vigentes')
        instituto_param = request.query_params.get('instituto_id')

        # Convertimos los valores
        vigentes = None
        if vigentes_param is not None:
            vigentes = vigentes_param.lower() in ['true', '1', 't', 'yes', 'y']

        instituto_id = int(instituto_param) if instituto_param else None

        # Consultamos el servicio
        carreras = carrera_service.listar_carreras(vigentes=vigentes, instituto_id=instituto_id)
        serializer = CarreraSerializer(carreras, many=True)

        # Mensaje intuitivo según el filtro
        msg = "Listado de carreras obtenido correctamente."
        if instituto_id and vigentes is not None:
            msg = f"Listado de carreras {'vigentes' if vigentes else 'no vigentes'} del instituto {instituto_id}."
        elif instituto_id:
            msg = f"Listado de carreras del instituto {instituto_id}."
        elif vigentes is not None:
            msg = f"Listado de carreras {'vigentes' if vigentes else 'no vigentes'}."

        return Response(serializer.data,status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["Gestión Académica - Carreras"],
        security=[{'Bearer': []}],
        operation_summary="Crear una nueva Carrera",
        operation_description="Permite al administrador registrar una nueva carrera universitaria.",
        request_body=CarreraCreateUpdateSerializer,
        responses={
            201: openapi.Response("Carrera creada correctamente", CarreraSerializer),
            400: "Error en los datos enviados"
        }
    )
    def post(self, request):
        datos = request.data.copy()
        if 'esta_vigente' not in datos:
            datos['esta_vigente'] = True

        serializer = CarreraCreateUpdateSerializer(data=datos)
        if serializer.is_valid():
            carrera = carrera_service.crear_carrera(serializer.validated_data)
            return Response({
                "message": "Carrera creada correctamente.",
                "data": CarreraSerializer(carrera).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "Error al crear la carrera.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
        

class CarreraDetailView(APIView):
    """Obtener, actualizar o eliminar una Carrera"""

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [(EsAdministrador | EsCoordinadorDeCarrera)()]
        return [AllowAny()]

    # ------------------------------
    # GET - Detalle de Carrera
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Carreras"],
        operation_summary="Obtener detalle de una Carrera",
        operation_description="Devuelve la información completa de una carrera específica, incluyendo el instituto al que pertenece.",
        responses={200: CarreraSerializer()}
    )
    def get(self, request, pk):
        carrera = carrera_service.obtener_carrera(pk)
        serializer = CarreraSerializer(carrera)
        return Response(serializer.data,status=status.HTTP_200_OK)

    # ------------------------------
    # PUT - Actualizar Carrera
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Carreras"],
        security=[{'Bearer': []}],
        operation_summary="Actualizar una Carrera",
        operation_description="Permite al administrador o al coordinador (activo de la carrera correspondiente) actualizar los datos de una carrera existente.",
        request_body=CarreraCreateUpdateSerializer,
        responses={
            200: openapi.Response("Carrera actualizada correctamente", CarreraSerializer),
            400: "Error en los datos enviados"
        }
    )
    def put(self, request, pk):
        carrera = carrera_service.obtener_carrera(pk)
        
        self.check_object_permissions(request, carrera)
        
        serializer = CarreraCreateUpdateSerializer(carrera, data=request.data, partial=True)
        if serializer.is_valid():
            carrera_actualizada = carrera_service.actualizar_carrera(pk, serializer.validated_data)
            return Response({
                "message": "Carrera actualizada correctamente.",
                "data": CarreraSerializer(carrera_actualizada).data
            })
        return Response({
            "message": "Error al actualizar la carrera.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # ------------------------------
    # DELETE - Eliminar Carrera (borrado lógico)
    # ------------------------------
    @swagger_auto_schema(
        tags=["Gestión Académica - Carreras"],
        security=[{'Bearer': []}],
        operation_summary="Eliminar una Carrera",
        operation_description="Permite al administrador marcar una carrera como no vigente (borrado lógico).",
        responses={200: "Carrera eliminada correctamente"}
    )
    def delete(self, request, pk):
        carrera = carrera_service.obtener_carrera(pk)
        self.check_object_permissions(request, carrera)
        carrera_service.eliminar_carrera(pk)
        return Response({
            "message": "Carrera eliminada correctamente (marcada como no vigente)."
        }, status=status.HTTP_200_OK)
        


class CarreraVigenciaUpdateView(APIView):
    """
    Activar o desactivar la vigencia de una carrera.
    Solo puede hacerlo un administrador.
    """

    def get_permissions(self):
        return [EsAdministrador()]

    @swagger_auto_schema(
        tags=["Gestión Académica - Carreras"],
        security=[{'Bearer': []}],
        operation_summary="Actualizar vigencia de una Carrera",
        operation_description="Permite al administrador actualizar la vigencia de una carrera.",
        request_body=CarreraVigenciaUpdateSerializer,
        responses={
            200: "Estado de vigencia actualizado correctamente.",
        }
    )
    def patch(self, request, pk):
        """Cambia el estado de vigencia (activa/inactiva) de una carrera"""
        try:
            carrera = carrera_service.obtener_carrera(pk)
        except carrera.DoesNotExist:
            return Response(
                {"message": "Carrera no encontrada."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CarreraSerializer(carrera, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            estado = "activada" if serializer.validated_data["esta_vigente"] else "desactivada"
            return Response({
                "message": f"La carrera fue {estado} correctamente.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "Error al cambiar la vigencia de la carrera.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

