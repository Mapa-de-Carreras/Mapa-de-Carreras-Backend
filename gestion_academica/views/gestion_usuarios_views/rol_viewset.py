from rest_framework import viewsets
# Usamos ReadOnlyModelViewSet porque solo queremos GET
from rest_framework.viewsets import ReadOnlyModelViewSet
# Decide el permiso. Si solo admins pueden ver roles:
from rest_framework.permissions import AllowAny

from ...models.M4_gestion_usuarios_autenticacion import Rol
from ...serializers.M4_gestion_usuarios_autenticacion import RolSerializer

class RolViewSet(ReadOnlyModelViewSet):
    """
    API endpoint que permite listar y ver los Roles del sistema.
    (Solo operaciones GET)
    """
    queryset = Rol.objects.all().order_by('id')
    serializer_class = RolSerializer
    # Usamos IsAdminUser para ser consistentes con tu UsuarioViewSet
    permission_classes = [AllowAny]