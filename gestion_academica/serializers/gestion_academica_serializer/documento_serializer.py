from rest_framework import serializers
from gestion_academica.models import Documento

        
class DocumentoDetailSerializer(serializers.ModelSerializer):
    archivo_url = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = ["id", "tipo", "emisor", "numero", "anio", "archivo", "archivo_url", "created_at"]
        read_only_fields = ["archivo_url", "created_at"]

    def get_archivo_url(self, obj):
        if obj.archivo:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.archivo.url)
        return None
    
    
    
    
class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ["id", "tipo", "emisor", "numero", "anio", "created_at"]