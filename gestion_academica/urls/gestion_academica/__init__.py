from django.urls import path, include

urlpatterns = [
    path('institutos/', include('gestion_academica.urls.gestion_academica.institutos')),
    path('carreras/', include('gestion_academica.urls.gestion_academica.carreras')),
    path('asignaturas/', include('gestion_academica.urls.gestion_academica.asignaturas')),
    path('planes/', include('gestion_academica.urls.gestion_academica.planes')),
    path('plan-asignatura/', include('gestion_academica.urls.gestion_academica.plan_asignatura')),
    path('documentos/', include('gestion_academica.urls.gestion_academica.documentos')),
]