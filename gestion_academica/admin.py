from django.contrib import admin
from .models import (
    Instituto, Carrera, Resolucion, Asignatura, PlanDeEstudio, PlanAsignatura,
    Correlativa, Cargo, Modalidad, Dedicacion, Docente, Coordinador,
    Comision, ParametrosRegimen, Designacion
)

# Registramos todos los modelos para que aparezcan en el panel de admin
admin.site.register(Instituto)
admin.site.register(Carrera)
admin.site.register(Resolucion)
admin.site.register(Asignatura)
admin.site.register(PlanDeEstudio)
admin.site.register(PlanAsignatura)
admin.site.register(Correlativa)
admin.site.register(Cargo)
admin.site.register(Modalidad)
admin.site.register(Dedicacion)
admin.site.register(Docente)
admin.site.register(Coordinador)
admin.site.register(Comision)
admin.site.register(ParametrosRegimen)
admin.site.register(Designacion)
