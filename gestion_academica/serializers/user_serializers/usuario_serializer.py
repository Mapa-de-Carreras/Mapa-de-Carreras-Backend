from rest_framework import serializers
from gestion_academica import models
from .base_usuario_serializer import BaseUsuarioSerializer
from ..M1_gestion_academica import CarreraSerializer
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

    carreras_coordinadas = serializers.SerializerMethodField()

    class Meta:
        model = models.Usuario
        # El Admin puede ver y editar todo
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active',
            'password', 'password2', 'legajo', 'fecha_nacimiento', 
            'celular', 'roles', 'carreras_coordinadas'
        ]
        extra_kwargs = {
            # Hacemos que la contraseña no sea requerida en PATCH
            'password': {'required': False}, 
            'password2': {'required': False},
            'fecha_nacimiento': {'required': True} # Sigue siendo req. para crear
        }
    
    def get_carreras_coordinadas(self, obj):
        """
        Si el usuario es un Coordinador, devuelve la lista de
        Carreras que tiene asignadas Y ACTIVAS.
        """
        # Comprobamos si el Usuario es un Coordinador
        if hasattr(obj, 'coordinador'):            
            # Accedemos al M2M 'carreras_coordinadas'
            # y filtramos usando la tabla 'through' (carreracoordinacion)
            # para traer solo las carreras donde la relación está 'activo=True'.
            carreras_activas = obj.coordinador.carreras_coordinadas.filter(
                carreracoordinacion__activo=True
            )
            
            # Usamos tu CarreraSerializer existente
            return CarreraSerializer(carreras_activas, many=True).data
        
        # Si no es coordinador, devuelve lista vacía
        return []

    def validate(self, data):
        """
        Validación de 'create' (contraseñas coinciden y complejidad).
        """
        # 1. Llama a la validación del padre (BaseUsuarioSerializer)
        data = super().validate(data)

        is_create = (self.instance is None) # Self.instance=Usuario si no es CREATE
        if is_create: # Se valida la contraseña solo si es CREATE
            if 'password' not in data or 'password2' not in data:
                 raise serializers.ValidationError({"password": "Password y password2 son requeridos para registrar."})
            validar_nueva_contraseña(data['password'], data['password2'])
        else:
            # Flujo de Update (PATCH por Admin)
            # NO permitimos cambiar la contraseña aquí.
            if 'password' in data or 'password2' in data:
                raise serializers.ValidationError({
                    "password": "No se puede cambiar la contraseña desde este endpoint. Use el flujo de reseteo de contraseña."
                })
        return data

    def create(self, validated_data):
        roles_data = validated_data.pop('roles', [])
        validated_data.pop('old_password', None)
        validated_data.pop('password2', None)

        # 1. Comprobamos si el rol "Coordinador" está en los roles ingresados
        es_coordinador = any(
            rol.nombre.lower() == 'coordinador' for rol in roles_data
        )

        es_docente = any(
            rol.nombre.lower() == 'docente' for rol in roles_data
        )

        if es_coordinador:
            # Si es Coordinador, creamos un objeto Coordinador (Source 4)
            model_manager = models.Coordinador.objects
        elif es_docente:
            # Si es Docente, creamos un objeto Docente
            model_manager = models.Docente.objects
        else:
            # Si no, creamos un Usuario (Source 4) normal
            model_manager = models.Usuario.objects

        usuario = model_manager.create_user(
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
    
    def to_representation(self, instance):
        """
        Sobrescribe la salida del serializer.
        Oculta 'carreras_coordinadas' si el usuario no es un Coordinador.
        """
        # 1. Obtiene la representación de datos estándar (diccionario)
        data = super().to_representation(instance)
        
        # 2. Comprueba si el usuario (instance) tiene el atributo 'coordinador'
        #    (Esto es más fiable que comprobar el rol aquí)
        if not hasattr(instance, 'coordinador'):
            # 3. Si NO es coordinador, quita el campo del diccionario
            data.pop('carreras_coordinadas', None)
        
        # 4. Devuelve el diccionario modificado
        return data