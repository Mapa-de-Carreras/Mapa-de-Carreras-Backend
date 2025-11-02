from gestion_academica import models
from .base_usuario_serializer import BaseUsuarioSerializer

class EditarUsuarioSerializer(BaseUsuarioSerializer):
    """
    Serializer para que un usuario (Coordinador, Docente)
    edite sus *propios* datos de perfil.
    """
    class Meta:
        model = models.Usuario
        # El usuario normal solo puede editar este subconjunto
        fields = [
            'first_name', 'last_name', 'username', 'email', 'celular', 'fecha_nacimiento',
        ]
        extra_kwargs = {
            'fecha_nacimiento': {'required': False},
        }

    # No necesita 'validate' ni 'update', los hereda de BaseUsuarioSerializer.
    # No necesita 'create', porque este serializer no es para registrar.