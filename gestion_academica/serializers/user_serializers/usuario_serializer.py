from rest_framework import serializers
from gestion_academica import models
from .base_usuario_serializer import BaseUsuarioSerializer
from ..validators import validar_nueva_contraseña

class CaseInsensitiveSlugRelatedField(serializers.SlugRelatedField):
    """
    Un SlugRelatedField que no distingue mayúsculas de minúsculas
    al buscar el 'slug' de rol en la base de datos.
    """
    def to_internal_value(self, data):
        # Sobrescribimos este método para usar una búsqueda
        # insensible a mayúsculas (__iexact)
        try:
            return self.get_queryset().get(**{
                f"{self.slug_field}__iexact": data
            })
        except (TypeError, ValueError):
            self.fail('invalid')
        except self.get_queryset().model.DoesNotExist:
            # Mensaje de error si no lo encuentra
            self.fail('does_not_exist', slug_name=self.slug_field, value=data)
        except self.get_queryset().model.MultipleObjectsReturned:
            # Mensaje de error si hay duplicados (ej: "rol" y "Rol")
            self.fail('multiple_objects')

class UsuarioSerializer(BaseUsuarioSerializer):
    """
    Serializer para el ADMIN. Puede ver y editar todos los campos
    y también crear usuarios.
    """
    roles = CaseInsensitiveSlugRelatedField(
        slug_field='nombre',  # Busca el rol por su campo 'nombre'
        queryset=models.Rol.objects.all(),
        many=True,
        required=False
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )

    class Meta:
        model = models.Usuario
        # El Admin puede ver y editar todo
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active',
            'password', 'password2', 'legajo', 'fecha_nacimiento', 
            'celular', 'roles'
        ]
        extra_kwargs = {
            # Hacemos que la contraseña no sea requerida en PATCH
            'password': {'required': False}, 
            'password2': {'required': False},
            'fecha_nacimiento': {'required': True} # Sigue siendo req. para crear
        }

    def validate(self, data):
        """
        Validación de 'create' (contraseñas coinciden y complejidad).
        """
        # 1. Llama a la validación del padre (BaseUsuarioSerializer)
        data = super().validate(data)
        # --- 2. USA LA LÓGICA CENTRALIZADA ---
        validar_nueva_contraseña(data['password'], data['password2'])
        return data

    def create(self, validated_data):
        roles_data = validated_data.pop('roles', [])
        validated_data.pop('old_password', None)
        validated_data.pop('password2', None)
    
        usuario = models.Usuario.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
            legajo=validated_data['legajo'],
            celular=validated_data['celular'],
            fecha_nacimiento=validated_data.get('fecha_nacimiento', None),
            is_active=False
        )
        
        for rol in roles_data:
            models.RolUsuario.objects.create(usuario=usuario, rol=rol)
            
        return usuario
    
    def update(self, instance, validated_data):
        """
        Maneja la actualización de roles (para Admin)
        y llama al 'update' de la base para los otros campos.
        """
        # 1. Extrae los roles antes de llamar al 'update' padre
        roles_data = validated_data.pop('roles', None)

        # 2. Llama al 'update' de BaseUsuarioSerializer
        #    para manejar todos los otros campos (email, nombre, etc.)
        instance = super().update(instance, validated_data)

        # 3. Si se enviaron roles, actualízalos
        if roles_data is not None:
            # .set() es la forma de Django de manejar ManyToMany
            instance.roles.set(roles_data)
        
        return instance