
from django.urls import path, include

from gestion_academica.views.debug_task import DebugEjecutarNotificacionesView

urlpatterns = [
    path('', include('gestion_academica.urls.gestion_academica')),
    path('', include('gestion_academica.urls.gestion_usuarios')),
    path('', include('gestion_academica.urls.gestion_designaciones')),
    path('', include("gestion_academica.urls.gestion_docentes")),
    path('debug/ejecutar-notificaciones/', DebugEjecutarNotificacionesView.as_view(), name='debug-ejecutar-notificaciones'),
]

