from django.urls import path, include

urlpatterns = [
    path('', include('gestion_academica.urls.gestion_academica')),
    path('', include('gestion_academica.urls.gestion_usuarios')),
    path('', include('gestion_academica.urls.gestion_designaciones'))
]