from rest_framework import serializers
from gestion_academica import models
from .base_usuario_serializer import BaseUsuarioSerializer

# --- MODIFICAMOS EL SERIALIZER DE DOCENTE ---
# Lo renombramos para que sea claro su propósito (editar)
class EditarDocenteSerializer(BaseUsuarioSerializer):
    """
    Serializer para editar los datos base de un Usuario
    Y los campos específicos del modelo Docente.
    """
    modalidad_id = serializers.PrimaryKeyRelatedField(
        source="modalidad",
        queryset=models.Modalidad.objects.all(),
        write_only=True, required=False, allow_null=True
    )
    caracter_id = serializers.PrimaryKeyRelatedField(
        source="caracter",
        queryset=models.Caracter.objects.all(),
        write_only=True, required=False, allow_null=True
    )
    dedicacion_id = serializers.PrimaryKeyRelatedField(
        source="dedicacion",
        queryset=models.Dedicacion.objects.all(),
        write_only=True, required=False, allow_null=True
    )

    # Campos de solo lectura para ver los objetos completos
    modalidad = serializers.StringRelatedField(read_only=True)
    caracter = serializers.StringRelatedField(read_only=True)
    dedicacion = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = models.Docente
        # Campos de Usuario (heredados de Base) + campos de Docente
        fields = [
            'first_name', 'last_name', 'username', 'email', 'celular', 'fecha_nacimiento',
            'modalidad', 'caracter', 'dedicacion', 'cantidad_materias',
            'modalidad_id', 'caracter_id', 'dedicacion_id'
        ]
        read_only_fields = ['modalidad', 'caracter', 'dedicacion']
        extra_kwargs = {
            'fecha_nacimiento': {'required': False},
        }
    
    # NO necesitamos 'validate' o 'update'.
    # BaseUsuarioSerializer.update() guardará mágicamente
    # los campos 'modalidad', 'caracter', etc.,
    # porque 'Docente' es un modelo hijo de 'Usuario'.