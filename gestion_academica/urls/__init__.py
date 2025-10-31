from django.urls import path, include

urlpatterns = [
    path('gestion-academica/', include('gestion_academica.urls.gestion_academica')),
    path('gestion-usuarios/', include('gestion_academica.urls.gestion_usuarios'))
]