# gestion_academica/views/documento_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from gestion_academica.serializers import DocumentoSerializer,DocumentoDetailSerializer
from gestion_academica.services import documentos as documento_service
class DocumentoListCreateView(APIView):

    @swagger_auto_schema(
        tags=["Gestión Académica - Documentos"],
        operation_summary="Listar documentos",
        responses={200: DocumentoSerializer(many=True)}
    )
    def get(self, request):
        documentos = documento_service.listar_documentos()
        serializer = DocumentoSerializer(documentos, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["Gestión Académica - Documentos"],
        operation_summary="Crear documento (probar UNICAMENTE en postman)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "tipo": openapi.Schema(type=openapi.TYPE_STRING),
                "emisor": openapi.Schema(type=openapi.TYPE_STRING),
                "numero": openapi.Schema(type=openapi.TYPE_STRING),
                "anio": openapi.Schema(type=openapi.TYPE_INTEGER),
                "archivo": openapi.Schema(type=openapi.TYPE_FILE),
            }
        ),
        responses={201: DocumentoSerializer()}
    )
    def post(self, request):
        serializer = DocumentoDetailSerializer(data=request.data)
        if serializer.is_valid():
            documento = serializer.save()
            return Response(DocumentoDetailSerializer(documento, context={"request": request}).data)
        return Response(serializer.errors, status=400)



class DocumentoDetailView(APIView):

    @swagger_auto_schema(
        tags=["Gestión Académica - Documentos"],
        operation_summary="Obtener detalle de un documento",
        responses={200: DocumentoSerializer()}
    )
    def get(self, request, pk):
        documento = documento_service.obtener_documento(pk)
        return Response(DocumentoDetailSerializer(documento, context={"request": request}).data)

    @swagger_auto_schema(
        tags=["Gestión Académica - Documentos"],
        operation_summary="Actualizar un documento (probar UNICAMENTE en postman)",
        request_body=DocumentoDetailSerializer,
        responses={200: DocumentoDetailSerializer()}
    )
    def put(self, request, pk):
        documento = documento_service.obtener_documento(pk)
        serializer = DocumentoDetailSerializer(documento, data=request.data, partial=False)
        if serializer.is_valid():
            documento = serializer.save()
            return Response(DocumentoDetailSerializer(documento, context={"request": request}).data)
        return Response(serializer.errors, status=400)
    
    @swagger_auto_schema(
        tags=["Gestión Académica - Documentos"],
        operation_summary="Actualizar un documento (parcialmente)",
        request_body=DocumentoSerializer,
        responses={200: DocumentoSerializer()}
    )
    
    def patch(self, request, pk):
        documento = documento_service.obtener_documento(pk)
        serializer = DocumentoSerializer(documento, data=request.data, partial=True)
        if serializer.is_valid():
            documento = serializer.save()
            return Response(DocumentoSerializer(documento).data)
        return Response(serializer.errors, status=400)
    
    

    @swagger_auto_schema(
        tags=["Gestión Académica - Documentos"],
        operation_summary="Eliminar un documento",
        responses={204: "Eliminado"}
    )
    def delete(self, request, pk):
        documento = documento_service.obtener_documento(pk)
        documento_service.eliminar_documento(documento)
        return Response(status=204)
