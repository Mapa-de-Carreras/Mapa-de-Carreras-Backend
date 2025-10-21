from django.contrib import admin
from django.urls import path, include

# --- Imports de Vistas ---
from rest_framework.routers import DefaultRouter
from gestion_academica.views.autenticacion_view import LoginView, LogoutView
from gestion_academica.views.usuario_view import UsuarioViewSet

# --- Imports de SimpleJWT ---
from rest_framework_simplejwt.views import TokenRefreshView

# --- Imports de DRF-YASG (Swagger) ---
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# --- Configuración de SWAGGER ---
schema_view = get_schema_view(
   openapi.Info(
      title="API de Mapa de Carreras", # Puedes cambiar este título
      default_version='v1',
      description="Documentación de la API para el proyecto",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# --- Configuración del ROUTER ---
# Esto crea las rutas para tu UsuarioViewSet
router = DefaultRouter()
router.register(r'api/usuarios', UsuarioViewSet, basename='usuario')


urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Endpoints de Autenticación (Login/Logout/Refresh) ---
    path('api/auth/login/', LoginView.as_view(), name='auth_login'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # Usamos la de simplejwt

    # --- Endpoints de Swagger ---
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redocs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # --- Endpoints de Gestión de Usuarios (CRUD y Registro) ---
    # Esto incluye /api/usuarios/ (POST para registro, GET para lista)
    path('', include(router.urls)),
]