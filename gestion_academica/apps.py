from django.apps import AppConfig
import sys


class GestionAcademicaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_academica'

    def ready(self):
        """
        - Registra señales SIEMPRE que Django carga la app.
        - Ejecuta tareas solo si el servidor real está corriendo.
        - Evita ejecución doble por el reloader de runserver.
        """

        # 1. Registrar señales (roles, catálogos, etc.)
        try:
            import gestion_academica.signals  # noqa
        except Exception as e:
            # Evitamos que errores de señales rompan migraciones
            print(f"[GESTION_ACADEMICA] Error al cargar señales: {e}")

        # 2. Detectar si estamos corriendo el servidor real (no migraciones)
        running_server = any(cmd in sys.argv for cmd in ['runserver', 'gunicorn', 'uwsgi'])

        if running_server:
            try:
                from .tasks import tasks
                tasks.iniciar_planificador_vencimientos()
                print("[GESTION_ACADEMICA] Planificador de vencimientos iniciado.")
            except Exception as e:
                print(f"[GESTION_ACADEMICA] Error al iniciar planificador: {e}")
