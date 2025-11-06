from rest_framework import serializers
from django.utils import timezone
from gestion_academica import models
from .base_usuario_serializer import BaseUsuarioSerializer
# Importamos los serializers que usaremos para mostrar datos
from ..M1_gestion_academica import CarreraSerializer

class EditarCoordinadorSerializer(BaseUsuarioSerializer):
    """
    Serializer para que un Coordinador edite sus datos de Usuario
    Y gestione su historial de asignación de carreras.
    """
    
    # --- CAMPO DE LECTURA (Read) ---
    # Para que el Coordinador VEA sus carreras al hacer GET /usuarios/{id}/
    carreras_coordinadas = serializers.SerializerMethodField()

    # --- CAMPO DE ESCRITURA (Write) ---
    # Este es el "Picker" para el frontend.
    # Acepta una lista de IDs de Carreras: [1, 2, 5]
    carreras_asignadas_ids = serializers.PrimaryKeyRelatedField(
        queryset=models.Carrera.objects.all(), # (Source 5)
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = models.Usuario
        # Campos del Usuario (Source 4) que puede editar (de EditarUsuarioSerializer (Source 6))
        fields = [
            'first_name', 'last_name', 'username', 'email', 'celular', 'fecha_nacimiento',
            # Los nuevos campos para las carreras
            'carreras_coordinadas', 'carreras_asignadas_ids'
        ]
        extra_kwargs = {
            'fecha_nacimiento': {'required': False},
        }

    def get_carreras_coordinadas(self, obj):
        """
        Muestra solo las carreras que el Coordinador tiene ACTIVAS.
        """
        if hasattr(obj, 'coordinador'): # (Source 4)
            carreras_activas = obj.coordinador.carreras_coordinadas.filter(
                carreracoordinacion__activo=True # (Source 4)
            )
            return CarreraSerializer(carreras_activas, many=True).data
        return []

    def update(self, instance, validated_data):
        # 'instance' es el objeto Usuario (Source 4)
        
        # 1. Obtenemos el objeto Coordinador (Source 4)
        try:
            coordinador_obj = instance.coordinador
        except models.Coordinador.DoesNotExist:
            # Si no es un coordinador, solo guardamos los datos del usuario
            # y no hacemos nada con las carreras.
            validated_data.pop('carreras_asignadas_ids', None) # Quitamos el campo de carreras
            return super().update(instance, validated_data)

        # 2. Extraemos la lista de carreras del "picker"
        # Si el frontend no envía 'carreras_asignadas_ids', no tocamos el historial
        if 'carreras_asignadas_ids' not in validated_data:
            return super().update(instance, validated_data)
            
        nuevas_carreras = validated_data.pop('carreras_asignadas_ids')
        nuevas_carreras_ids = set(carrera.id for carrera in nuevas_carreras)

        # 3. Guardamos los campos del usuario (first_name, email, etc.)
        instance = super().update(instance, validated_data)

        # --- 4. LÓGICA DE HISTORIAL (La parte importante) ---
        
        # Obtenemos las asignaciones activas actuales
        asignaciones_actuales = models.CarreraCoordinacion.objects.filter(
            coordinador=coordinador_obj,
            activo=True
        )
        carreras_actuales_ids = set(asignacion.carrera_id for asignacion in asignaciones_actuales)

        # Calculamos qué hacer
        ids_para_desactivar = carreras_actuales_ids - nuevas_carreras_ids
        ids_para_activar = nuevas_carreras_ids - carreras_actuales_ids
        
        # 4a. Desactivar asignaciones antiguas
        if ids_para_desactivar:
            models.CarreraCoordinacion.objects.filter(
                coordinador=coordinador_obj,
                carrera_id__in=ids_para_desactivar,
                activo=True
            ).update(activo=False, fecha_fin=timezone.now())

        # 4b. Crear nuevas asignaciones
        # Necesitamos el usuario que hizo el cambio (el propio coordinador)
        usuario_que_asigna = self.context['request'].user
        
        nuevas_asignaciones_obj = []
        for carrera_id in ids_para_activar:
            nuevas_asignaciones_obj.append(
                models.CarreraCoordinacion(
                    coordinador=coordinador_obj,
                    carrera_id=carrera_id,
                    activo=True,
                    fecha_inicio=timezone.now(),
                    creado_por=usuario_que_asigna # (Source 4)
                )
            )
        
        if nuevas_asignaciones_obj:
            models.CarreraCoordinacion.objects.bulk_create(nuevas_asignaciones_obj)
        
        return instance