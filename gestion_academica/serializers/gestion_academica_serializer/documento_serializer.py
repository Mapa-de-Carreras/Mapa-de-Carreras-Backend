from rest_framework import serializers
from gestion_academica.models import Documento

class ArchivoUploadSerializer(serializers.Serializer):
    ruta = serializers.CharField()
    archivo = serializers.FileField()
    
    
class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = [
            "id", "tipo", "emisor", "numero", "anio",
            "archivo", "created_at"
        ]
        read_only_fields = ["id", "created_at"]