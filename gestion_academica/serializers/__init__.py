# gestion_academica/serializers/__init__.py

from .M1_gestion_academica import (
    InstitutoSerializer, CarreraSerializer, AsignaturaSerializer,
    DocumentoSerializer, PlanAsignaturaSerializer, PlanDeEstudioSerializer,
    CorrelativaSerializer, ResolucionSerializer
)

from .M4_gestion_usuarios_autenticacion import (
    RolUsuarioSerializer, RolSerializer,
    NotificacionSerializer, UsuarioNotificacionSerializer,
)

from .M2_gestion_docentes import (
    DocenteSerializer, ModalidadSerializer, DedicacionSerializer,
    CaracterSerializer, ParametrosRegimenSerializer
)

from .M3_designaciones_docentes import (
    DesignacionSerializer, ComisionSerializer, CargoSerializer
)
from .auth_serializers.activar_cuenta_serializer import ActivarCuentaSerializer
from .auth_serializers.enviar_codigo_verificacion_serializer import EnviarCodigoVerificacionSerializer
from .auth_serializers.recuperar_username_serializer import RecuperarUsuarioSerializer
from .auth_serializers.restablecer_contrasena_serializer import RestablecerContraseñaSerializer

from .user_serializers.editar_usuario_serializer import EditarUsuarioSerializer
from .user_serializers.editar_docente_serializer import EditarDocenteSerializer
from .user_serializers.editar_coordinador_serializer import EditarCoordinadorSerializer
from .user_serializers.usuario_serializer import UsuarioSerializer, AdminUsuarioDetalleSerializer, CoordinadorSerializer, CarreraCoordinacionSerializer
from .M1_gestion_academica import InstitutoSerializer
