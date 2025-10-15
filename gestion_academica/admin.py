# gestion_academica/admin.py

from django.contrib import admin
from .models import (
    Instituto, Carrera, Resolucion, Asignatura, PlanDeEstudio, PlanAsignatura,
    Correlativa, Comision, Rol, Usuario, RolUsuario, Notificacion,
    UsuarioNotificacion, Caracter, Modalidad, Cargo, Docente,
    CarreraCoordinacion, Coordinador, Dedicacion, ParametrosRegimen, Designacion
)

# Registra todos los modelos para que aparezcan en el panel de admin.
modelos_a_registrar = [
    Instituto, Carrera, Resolucion, Asignatura, PlanDeEstudio, PlanAsignatura,
    Correlativa, Comision, Rol, Usuario, RolUsuario, Notificacion,
    UsuarioNotificacion, Caracter, Modalidad, Cargo, Docente,
    CarreraCoordinacion, Coordinador, Dedicacion, ParametrosRegimen, Designacion
]

for modelo in modelos_a_registrar:
    admin.site.register(modelo)
