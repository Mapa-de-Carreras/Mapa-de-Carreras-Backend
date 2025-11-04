from django.urls import path

from gestion_academica.views.gestion_academica_views.institutos import *

urlpatterns = [
    path('', InstitutoListCreateView.as_view(), name='instituto-list-create'),
    path('<int:pk>/', InstitutoDetailView.as_view(), name='instituto-detail'),
]