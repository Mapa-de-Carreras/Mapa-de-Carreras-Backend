from django.urls import path
from gestion_academica.views import (
    UsuarioRegistroView,
    SolicitarCodigoView,
    ActivarCuentaView,
    RestablecerContraseñaView,
    RecuperarUsuarioView,
    LoginView,
    LogoutView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.permissions import AllowAny

urlpatterns = [

    # --- Endpoints de Autenticación (Login/Logout/Refresh) ---
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(permission_classes=[AllowAny]), name='token_refresh'), # Usamos la de simplejwt

    # --- Endpoints de flujo de Registro ---
    path('auth/registrar-usuario/', UsuarioRegistroView.as_view(), name='registrar_usuario'),
    path('auth/registrar/activar-cuenta/', ActivarCuentaView.as_view(), name='activar_cuenta'),

    # --- Flujo de Recuperación de Cuenta ---
    path('auth/recuperar/solicitar-codigo/', SolicitarCodigoView.as_view(), name='solicitar_codigo_verificacion'), 
    path('auth/recuperar/restablecer-contraseña/', RestablecerContraseñaView.as_view(), name='restablecer_contraseña'),
    path('auth/recuperar/recuperar-username/', RecuperarUsuarioView.as_view(), name='recuperar_username'),

]