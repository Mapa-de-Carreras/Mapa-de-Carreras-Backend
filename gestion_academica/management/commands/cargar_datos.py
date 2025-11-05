from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Carga fixtures de gestión académica y gestión de usuarios en orden lógico'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write(self.style.NOTICE("Cargando fixtures..."))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_institutos.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de INSTITUTOS cargados ✅"))
            
            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_carreras.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de CARRERAS cargados ✅"))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_resoluciones.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de RESOLUCIONES cargados ✅"))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_documentos.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de DOCUMENTOS cargados ✅"))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_asignaturas.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de ASIGNATURAS cargados ✅"))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_planesdeestudio.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de PLANES DE ESTUDIOS cargados ✅"))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_planasignaturas.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de PLANES DE ASIGNATURAS cargados ✅"))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_academica_correlativas.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de CORRELATIVAS cargados ✅"))

            call_command('loaddata', 'gestion_academica/fixtures/data_gestion_usuarios_inicial.json')
            self.stdout.write(self.style.SUCCESS("Datos iniciales de gestión de usuarios cargados ✅"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error al cargar fixtures: {e}"))
