from rest_framework import serializers
from gestion_academica.models import Instituto


class InstitutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instituto
        fields = ['id', 'codigo', 'nombre', 'activo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at','activo']
        
    def validate(self, data):
        if 'activo' not in data:
            data['activo'] = True
        return data

    def validate_codigo(self, value):
        if Instituto.objects.filter(codigo=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Ya existe un instituto con este código.")
        return value

    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre del instituto no puede estar vacío.")
        return value