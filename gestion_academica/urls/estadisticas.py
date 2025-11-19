from django.urls import path

from gestion_academica.views.estadisticas_reportes_views.estadisticas import (
    DocentesPorDedicacionAPIView,
    DocentesPorModalidadAPIView,
    HorasPorDocenteAPIView,
    DesignacionesPorCarreraAPIView,
    HistorialDocenteAPIView,
)
from gestion_academica.views.estadisticas_reportes_views.reportes import (
    ExportarEstadisticasAPIView,
)

urlpatterns = [
    path("estadisticas/docentes/dedicacion/", DocentesPorDedicacionAPIView.as_view()),
    path("estadisticas/docentes/modalidad/", DocentesPorModalidadAPIView.as_view()),
    path("estadisticas/docentes/horas/", HorasPorDocenteAPIView.as_view()),
    path("estadisticas/designaciones/", DesignacionesPorCarreraAPIView.as_view()),
    path(
        "estadisticas/docente/<int:docente_id>/historial/",
        HistorialDocenteAPIView.as_view(),
    ),
    path("estadisticas/exportar/", ExportarEstadisticasAPIView.as_view()),
]
