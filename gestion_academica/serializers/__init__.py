# gestion_academica/serializers/__init__.py

from .M1_gestion_academica import (
    InstitutoSerializer, CarreraSerializer, AsignaturaSerializer,
    DocumentoSerializer, PlanAsignaturaSerializer, PlanDeEstudioSerializer,
    CorrelativaSerializer, ResolucionSerializer
)

from .M4_gestion_usuarios_autenticacion import (
    UsuarioSerializer, RolUsuarioSerializer, RolSerializer,
    NotificacionSerializer, UsuarioNotificacionSerializer,
    CarreraCoordinacionSerializer, CoordinadorSerializer
)

from .M2_gestion_docentes import (
    DocenteSerializer, ModalidadSerializer, DedicacionSerializer,
    CaracterSerializer, ParametrosRegimenSerializer
)

from .M3_designaciones_docentes import (
    DesignacionSerializer, ComisionSerializer, CargoSerializer
)
from .auth_serializers import ActivarCuentaSerializer, EnviarCodigoVerificacionSerializer, RecuperarUsuarioSerializer, RestablecerContraseñaSerializer

from .user_serializers import UsuarioSerializer, EditarCoordinadorSerializer, EditarDocenteSerializer, EditarUsuarioSerializer
from .M1_gestion_academica import InstitutoSerializer
