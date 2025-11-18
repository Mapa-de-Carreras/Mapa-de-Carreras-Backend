from django.utils import timezone
from rest_framework import serializers
from gestion_academica import models
from .base_usuario_serializer import BaseUsuarioSerializer
from gestion_academica.serializers import CarreraSerializerDetail
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
        """
        Crea un nuevo Usuario y sus perfiles de Docente/Coordinador
        basado en los roles asignados.
        """
        
        # 1. Extrae roles y contraseñas
        roles_data = validated_data.pop('roles', [])
        password = validated_data.pop('password')
        validated_data.pop('password2', None) # Ya validado en .validate()

        # 2. SIEMPRE crea un 'Usuario' base
        # Usamos create_user para hashear la contraseña correctamente
        # (Uso los campos de tu create original)
        usuario = models.Usuario.objects.create_user(
            username=validated_data['username'],
            password=password,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            email=validated_data.get('email', ''),
            legajo=validated_data.get('legajo'),
            celular=validated_data.get('celular'),
            fecha_nacimiento=validated_data.get('fecha_nacimiento', None),
            is_active=False # El create original los ponía en False
        )
        
        # 3. Asigna los roles en la tabla RolUsuario
        usuario.roles.set(roles_data)

        # 4. Crea los perfiles vacíos si los roles existen
        rol_nombres = [rol.nombre.lower() for rol in roles_data]
        
        if "docente" in rol_nombres:
            models.Docente.objects.create(usuario=usuario, activo=True)
            
        if "coordinador" in rol_nombres:
            models.Coordinador.objects.create(usuario=usuario, activo=True)
            
        return usuario
    
    def update(self, instance, validated_data):
        """
        Maneja la actualización de roles (para Admin)
        y llama al 'update' de la base para los otros campos.
        
        Añade lógica para desactivar carreras si se quita el rol
        de Coordinador.
        """
        
        # 1. Extrae los roles antes de llamar al 'update' padre
        roles_data = validated_data.pop('roles', None)

        rol_coordinador = None
        era_coordinador = False
        rol_docente = None
        era_docente = False
        if roles_data is not None:
            # Revisa los roles que el usuario TENÍA ANTES
            try:
                rol_coordinador = models.Rol.objects.get(nombre__iexact="COORDINADOR")
                era_coordinador = instance.roles.filter(pk=rol_coordinador.pk).exists()
                rol_docente = models.Rol.objects.get(nombre__iexact="DOCENTE")
                era_docente = instance.roles.filter(pk=rol_docente.pk).exists()
            except models.Rol.DoesNotExist:
                pass # El rol no existe, no hay nada que hacer

        # 2. Llama al 'update' de BaseUsuarioSerializer
        #    para manejar todos los otros campos (email, nombre, etc.)
        instance = super().update(instance, validated_data)

        # 3. Si se enviaron roles, actualízalos
        if roles_data is not None:
            # .set() es la forma de Django de manejar ManyToMany
            # Esto maneja borrar RolUsuario
            instance.roles.set(roles_data)

            # Obtener los nombres de los NUEVOS roles
            rol_nombres_nuevos = [rol.nombre.lower() for rol in roles_data]
            if "docente" in rol_nombres_nuevos:
                docente_perfil, _ = models.Docente.objects.get_or_create(usuario=instance)
                if hasattr(docente_perfil, 'activo') and not docente_perfil.activo:
                    docente_perfil.activo = True
                    docente_perfil.save()
            
            if "coordinador" in rol_nombres_nuevos:
                coordinador_perfil, _ = models.Coordinador.objects.get_or_create(usuario=instance)
                if hasattr(coordinador_perfil, 'activo') and not coordinador_perfil.activo:
                    coordinador_perfil.activo = True
                    coordinador_perfil.save()
            
            # --- 3d. Lógica de Desactivación (Ejecución) ---
            if era_coordinador and "coordinador" not in rol_nombres_nuevos:
                if hasattr(instance, 'coordinador'): 
                    coordinador_perfil = instance.coordinador
                    # ¡Se le quitó el rol! Desactivar todas sus carreras activas.
                    models.CarreraCoordinacion.objects.filter(
                        coordinador=coordinador_perfil, 
                        activo=True
                    ).update(activo=False, fecha_fin=timezone.now())
                if hasattr(coordinador_perfil, 'activo'):
                    coordinador_perfil.activo = False
                    coordinador_perfil.save()
            # Lógica de desactivación docente
            if era_docente and "docente" not in rol_nombres_nuevos:
                if hasattr(instance, 'docente'):
                    docente_perfil = instance.docente
                    
                    # Deshabilitar el perfil del Docente
                    if hasattr(docente_perfil, 'activo'):
                        docente_perfil.activo = False
                        docente_perfil.save()

        return instance
    
class CarreraCoordinacionSerializer(serializers.ModelSerializer):
    carrera = serializers.StringRelatedField(
        read_only=True
    )
    carrera_id = serializers.PrimaryKeyRelatedField(
        source="carrera",
        queryset=models.Carrera.objects.all(),
        write_only=True
    )

    coordinador = serializers.StringRelatedField(read_only=True)
    coordinador_id = serializers.PrimaryKeyRelatedField(
        source="coordinador",
        queryset=models.Coordinador.objects.all(),
        write_only=True
    )

    creado_por = serializers.StringRelatedField(read_only=True)
    creado_por_id = serializers.PrimaryKeyRelatedField(
        source="creado_por",
        queryset=models.Usuario.objects.all(),
        write_only=True
    )

    class Meta:
        model = models.CarreraCoordinacion
        fields = [
            'id', 'carrera', 'carrera_id', 'coordinador', 'coordinador_id',
            'fecha_inicio', 'fecha_fin', 'activo', 'creado_por', 'creado_por_id'
        ]
    
class CoordinadorSerializer(serializers.ModelSerializer):
    carreras_coordinadas = serializers.SerializerMethodField()

    class Meta:
        model = models.Coordinador
        fields = [
            'id', 'carreras_coordinadas', 'usuario_id'
        ]

    def get_carreras_coordinadas(self, instance):
        """
        'instance' es el objeto Coordinador.
        Este método filtra y devuelve solo las asignaciones
        de CarreraCoordinacion que están activas.
        """
        
        # Filtramos el 'carreracoordinacion_set' por activo=True
        asignaciones_activas = instance.carreracoordinacion_set.filter(
            activo=True
        )
        
        # Usamos el CarreraCoordinacionSerializer (que ya tenías)
        # para serializar la lista filtrada
        return CarreraCoordinacionSerializer(asignaciones_activas, many=True).data

class AdminUsuarioDetalleSerializer(UsuarioSerializer):
    """
    Serializer de SÓLO LECTURA para que el Admin vea
    el perfil COMPLETO de un usuario, incluyendo sus
    datos de Docente o Coordinador (si los tiene).
    """
    
    # SerializerMethodField para cargar dinámicamente
    # los datos del rol específico.
    docente_data = serializers.SerializerMethodField(read_only=True)
    coordinador_data = serializers.SerializerMethodField(read_only=True)

    class Meta(UsuarioSerializer.Meta):
        # Hereda todos los fields de UsuarioSerializer
        # y añade los nuevos.
        fields = UsuarioSerializer.Meta.fields + [
            'docente_data', 'coordinador_data'
        ]

    def get_docente_data(self, obj):
        from ..M2_gestion_docentes import DocenteSerializer
        """
        Si el usuario tiene un perfil de docente,
        lo serializa y lo devuelve.
        """
        # hasattr() comprueba si existe el "hijo" (Docente)
        if hasattr(obj, 'docente'):
            # Usamos el serializer de detalle de Docente
            return DocenteSerializer(obj.docente).data
        return None

    def get_coordinador_data(self, obj):
        """
        Si el usuario tiene un perfil de coordinador,
        lo serializa y lo devuelve.
        """
        if hasattr(obj, 'coordinador'):
            # Usamos el serializer de Coordinador
            return CoordinadorSerializer(obj.coordinador).data
        return None