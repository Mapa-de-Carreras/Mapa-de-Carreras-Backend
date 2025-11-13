from django.apps import AppConfig
import sys

class GestionAcademicaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_academica'

    def ready(self):
        # Evita que se ejecute dos veces (ej. en el 'runserver' y el 'reloader')
        # También evitamos que corra durante las migraciones
        running_server = any(cmd in sys.argv for cmd in ['runserver', 'gunicorn', 'uwsgi'])

        if running_server:
            from .tasks import tasks
            tasks.iniciar_planificador_vencimientos()