from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from gestion_academica.models import UsuarioNotificacion
from gestion_academica.serializers.user_serializers.notificaciones_serializer import UsuarioNotificacionSerializer

class NotificacionesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class MisNotificacionesViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    Endpoint para que el usuario logueado gestione sus notificaciones.
    """
    serializer_class = UsuarioNotificacionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificacionesPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'leida', 
                openapi.IN_QUERY, 
                description="Filtrar notificaciones: true=Leídas, false=No leídas", 
                type=openapi.TYPE_BOOLEAN
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Listar notificaciones (Sobreescrito para documentar el filtro).
        """
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        ahora = timezone.now()
        
        queryset = UsuarioNotificacion.objects.filter(
            usuario=user,
            eliminado=False,
        ).filter(
            Q(fecha_recordatorio__isnull=True) | Q(fecha_recordatorio__lte=ahora)
        ).order_by('-notificacion__fecha_creacion')

        leida_param = self.request.query_params.get('leida', None)
        
        if leida_param is not None:
            
            val = str(leida_param).strip().lower()
            
            if val == 'true':
                queryset = queryset.filter(leida=True)
            elif val == 'false':
                queryset = queryset.filter(leida=False)
        
        return queryset

    # --- ACCIONES

    @swagger_auto_schema(
        operation_summary="Marcar como leída",
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT), 
        responses={200: "OK"}
    )
    @action(detail=True, methods=['patch'])
    def leer(self, request, pk=None):
        usuario_notificacion = self.get_object()
        if not usuario_notificacion.leida:
            usuario_notificacion.leida = True
            usuario_notificacion.fecha_leida = timezone.now()
            usuario_notificacion.save()
        return Response({'status': 'leida'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Posponer 7 días",
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT), 
        responses={200: "OK"}
    )
    @action(detail=True, methods=['patch'])
    def posponer(self, request, pk=None):
        usuario_notificacion = self.get_object()
        usuario_notificacion.fecha_recordatorio = timezone.now() + timedelta(days=7) 
        usuario_notificacion.save()
        return Response({'status': 'pospuesta'}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Archivar",
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT), 
        responses={200: "OK"}
    )
    @action(detail=True, methods=['patch'])
    def archivar(self, request, pk=None):
        usuario_notificacion = self.get_object()
        usuario_notificacion.eliminado = True
        usuario_notificacion.save()
        return Response({'status': 'archivada'}, status=status.HTTP_200_OK)