import django_filters
from ..models import Usuario

class UsuarioFilter(django_filters.FilterSet):
    """
    Clase de filtro explícita para el ViewSet de Usuarios.
    """
    
    # Define 'is_active' como un filtro booleano
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    # Define 'username' como un filtro de texto (ignora mayúsculas)
    username = django_filters.CharFilter(field_name='username', lookup_expr='iexact')
    
    # Define 'email' como un filtro de texto (ignora mayúsculas)
    email = django_filters.CharFilter(field_name='email', lookup_expr='iexact')

    class Meta:
        model = Usuario
        # Lista los campos que Django Filter debe manejar
        fields = ['is_active', 'username', 'email']