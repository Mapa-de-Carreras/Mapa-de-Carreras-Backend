# gestion_academica/urls/__init__.py
from django.urls import include, path

urlpatterns = [
    path("", include("gestion_academica.urls.M2_gestion_docentes"))
]
