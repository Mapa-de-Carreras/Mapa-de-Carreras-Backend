from rest_framework import serializers
from gestion_academica import models

class UsuarioNotificacionSerializer(serializers.ModelSerializer):

    titulo = serializers.CharField(source='notificacion.titulo', read_only=True)
    mensaje = serializers.CharField(source='notificacion.mensaje', read_only=True)
    tipo = serializers.CharField(source='notificacion.tipo', read_only=True)
    fecha_emision = serializers.DateTimeField(source='notificacion.fecha_creacion', read_only=True)
    
    emitido_por = serializers.SerializerMethodField()

    class Meta:
        model = models.UsuarioNotificacion
        fields = [
            'id', 
            'titulo', 
            'mensaje', 
            'tipo', 
            'emitido_por',     
            'fecha_emision', 
            'leida', 
            'fecha_recordatorio'
        ]

    def get_emitido_por(self, obj):
        """
        Devuelve el nombre del creador o 'Sistema' si es automático.
        obj es la instancia de UsuarioNotificacion.
        """
        creador = obj.notificacion.creado_por
        
        if creador:
            nombre_completo = f"{creador.first_name} {creador.last_name}".strip()
            return nombre_completo if nombre_completo else creador.username
        
        return "Sistema"