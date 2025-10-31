from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.shortcuts import redirect

schema_view = get_schema_view(
   openapi.Info(
      title="API Mapa de Carreras",
      default_version='v1',
      description="Documentación general de la API",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', lambda request: redirect('swagger-ui', permanent=False)), 
    path('admin/', admin.site.urls),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redocs/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc-ui'),
    path('api/', include('gestion_academica.urls')),
]
