from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .notificar_vencimientos_designaciones import notificar_vencimientos_designaciones
from .notificar_materias_sin_responsable import notificar_materias_sin_responsable

# --- 1. CONFIGURACIÓN DEL PLANIFICADOR (SCHEDULER) ---

def iniciar_planificador_vencimientos():
    """Inicia el planificador de tareas en segundo plano."""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Ejecuta la tarea 1 vez al día
    # Aquí está programado para ejecutarse todos los días a las 2:00 AM.

    # --- NOTIFICAR VENCIMIENTOS DESIGNACIONES ---
    scheduler.add_job(
        notificar_vencimientos_designaciones,
        trigger='cron',
        hour='2',
        minute='0',
        id='notificar_vencimientos_designaciones', # ID único para el job
        jobstore='default',
        replace_existing=True,
    )
    # --- NOTIFICAR MATERIAS SIN RESPONSABLE ---
    # La ejecutamos a una hora distinta: 3:00 AM
    scheduler.add_job(
        notificar_materias_sin_responsable,
        trigger='cron',
        hour='3',
        minute='0',
        id='notificar_materias_sin_responsable',
        jobstore='default',
        replace_existing=True,
    )
    
    try:
        scheduler.start()
    except Exception as e:
        print(f"Error al iniciar el planificador de vencimientos: {e}")