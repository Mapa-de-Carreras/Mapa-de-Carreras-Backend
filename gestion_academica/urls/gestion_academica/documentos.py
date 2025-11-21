# gestion_academica/urls.py

from django.urls import path
from gestion_academica.views.gestion_academica_views.documentos import DocumentoListCreateView, DocumentoDetailView

urlpatterns = [
    path("/", DocumentoListCreateView.as_view(), name="documentos"),
    path("/<int:pk>/", DocumentoDetailView.as_view(), name="documento-detalle"),
]
