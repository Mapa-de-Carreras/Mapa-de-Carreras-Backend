from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from datetime import timedelta
from gestion_academica import models

# --- 1. CONFIGURACIÓN DEL PLANIFICADOR (SCHEDULER) ---

def iniciar_planificador_vencimientos():
    """Inicia el planificador de tareas en segundo plano."""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Paso 1 (Flujo principal): Ejecuta la tarea 1 vez al día
    # Aquí está programado para ejecutarse todos los días a las 2:00 AM.
    scheduler.add_job(
        notificar_vencimientos_designaciones,
        trigger='cron',
        hour='2',
        minute='0',
        id='notificar_vencimientos_designaciones', # ID único para el job
        jobstore='default',
        replace_existing=True,
    )
    
    try:
        scheduler.start()
    except Exception as e:
        print(f"Error al iniciar el planificador de vencimientos: {e}")


# --- 2. LA TAREA (LA LÓGICA DEL CASO DE USO) ---

def notificar_vencimientos_designaciones():
    """
    Busca designaciones próximas a vencer (30 días) y notifica
    a los coordinadores de carrera correspondientes.
    """
    print(f"[{timezone.now()}] Ejecutando tarea: notificar_vencimientos_designaciones...")
    
    # Definir el rango de fechas
    hoy = timezone.now()
    treinta_dias = hoy + timedelta(days=30)

    # Paso 2 (Flujo principal): Consulta designaciones activas
    # con fecha_vencimiento (fecha_fin) dentro de los próximos 30 días
    designaciones_por_vencer = models.Designacion.objects.filter(
        fecha_fin__gte=hoy,
        fecha_fin__lte=treinta_dias
    ).select_related(
        # 1. Optimizamos las relaciones ForeignKey (1-a-1)
        'comision__asignatura'
    ).prefetch_related(
        # 2. Optimizamos las relaciones ManyToMany (N-a-N)
        'comision__asignatura__planes_de_estudio__carrera'
    )

    if not designaciones_por_vencer.exists():
        # Paso 2 (Flujo secundario): Sin designaciones vencidas
        print("No se encontraron designaciones próximas a vencer.")
        return

    # Usamos un diccionario para agrupar notificaciones por coordinador
    # {coordinador_obj: {designacion1, designacion2, ...}}
    notificaciones_a_enviar = {}

    for desig in designaciones_por_vencer:
        # --- Ruta de Modelos para encontrar la Carrera ---
        # Designacion -> Comision -> Asignatura
        asignatura = desig.comision.asignatura
        
        # Asignatura -> PlanDeEstudio (vía M2M 'planes_de_estudio')
        planes = asignatura.planes_de_estudio.all()
        
        # PlanDeEstudio -> Carrera
        carreras_de_la_asignatura = set()
        for plan in planes:
            if plan.carrera:
                carreras_de_la_asignatura.add(plan.carrera)

        if not carreras_de_la_asignatura:
            continue # Esta asignatura no está en ningún plan con carrera

        # --- Encontrar al Coordinador ---
        for carrera in carreras_de_la_asignatura:
            # Carrera -> Coordinador (vía M2M 'carreras_coordinadas')
            # Buscamos coordinadores que estén activos en esa carrera
            coordinadores_activos = models.Coordinador.objects.filter(
                carreras_coordinadas=carrera,         # Relación M2M
                carreracoordinacion__carrera=carrera, # Filtro en la tabla 'through'
                carreracoordinacion__activo=True,     # Filtro 'activo' en 'through'
                activo=True                           # Perfil de Coordinador activo
            ).distinct()

            for coord in coordinadores_activos:
                if coord not in notificaciones_a_enviar:
                    notificaciones_a_enviar[coord] = set()
                # Agrupamos todas las designaciones para este coordinador
                notificaciones_a_enviar[coord].add(desig)

    # Paso 3 y 4 (Flujo principal): Generar y registrar las notificaciones
    for coordinador, designaciones_set in notificaciones_a_enviar.items():
        
        conteo = len(designaciones_set)
        plural = "s" if conteo > 1 else ""
        titulo = "Vencimiento de Designaciones"
        # Usamos un mensaje genérico que agrupa todas las designaciones
        mensaje = (
            f"Tiene {conteo} designacion{plural} de su carrera próxima{plural} "
            f"a vencer en los próximos 30 días. Revíselas aquí."
        )

        # Creamos la Notificación (el contenido)
        notif_obj, _ = models.Notificacion.objects.get_or_create(
            titulo=titulo,
            mensaje=mensaje,
            tipo="ALERTA", # Paso 4
            # creado_por puede ser null o un usuario "Sistema" si lo tienes
        )

        # Creamos la UsuarioNotificacion (la asignación)
        # Usamos el 'usuario' del perfil Coordinador
        un, created = models.UsuarioNotificacion.objects.get_or_create(
            usuario=coordinador.usuario, 
            notificacion=notif_obj
        )

        # --- Lógica de Reiteración y Recordatorios ---
        if created:
            # Es nueva, el coordinador la verá.
            print(f"Notificación nueva creada para {coordinador.usuario.username}")
        
        elif un.leida or un.eliminado:
            # Paso 7 ("Marcar como revisada")
            # El coordinador ya la leyó o descartó, no lo molestamos.
            continue
            
        elif un.fecha_recordatorio and un.fecha_recordatorio > hoy:
            # Paso 7 ("Recordar más tarde")
            # El coordinador pidió un recordatorio y aún no es la fecha.
            continue
            
        else:
            # La notificación ya existe, no fue leída, y no está pospuesta.
            # La "reactivamos" para que vuelva a aparecer.
            # Esto cumple con "se reitera"
            un.leida = False
            un.eliminado = False
            un.fecha_recordatorio = None # Limpiamos el recordatorio
            un.save()
            print(f"Notificación reactivada para {coordinador.usuario.username}")

    print(f"[{timezone.now()}] Tarea 'notificar_vencimientos_designaciones' completada.")

    # Paso 2: Consulta de designaciones activas próximas a vencer
    # (Paso 2 del Flujo Principal)
    designaciones = models.Designacion.objects.filter(
        fecha_fin__gte=hoy,          # Aún no ha vencido
        fecha_fin__lte=treinta_dias  # Vence dentro de los 30 días
    ).select_related(
        # 1. Optimizamos las relaciones ForeignKey (1-a-1)
        'comision__asignatura'
    ).prefetch_related(
        # 2. Optimizamos las relaciones ManyToMany (N-a-N)
        'comision__asignatura__planes_de_estudio__carrera'
    )

    if not designaciones.exists():
        # Flujo secundario 2
        print("No se encontraron designaciones próximas a vencer.")
        return

    # Paso 3: Agrupar por Coordinador (para no enviar spam)
    # {coordinador_obj: {designacion1, designacion2}}
    notificaciones_a_enviar = {}

    for desig in designaciones:
        try:
            # ASUMO esta ruta
            carrera = desig.comision.asignatura.plan_de_estudio.carrera
        except AttributeError:
            # Si una designación no tiene carrera (ej: datos de prueba), la saltamos
            continue

        # Encontrar todos los coordinadores ACTIVOS de esa carrera
        coordinadores_activos = models.Coordinador.objects.filter(
            carreras_coordinadas=carrera,
            carreracoordinacion__carrera=carrera,
            carreracoordinacion__activo=True,
            activo=True # El perfil del coordinador también debe estar activo
        ).distinct()

        for coord in coordinadores_activos:
            if coord not in notificaciones_a_enviar:
                notificaciones_a_enviar[coord] = set()
            notificaciones_a_enviar[coord].add(desig)

    # Paso 4: Generar y registrar las notificaciones
    for coordinador, designaciones_set in notificaciones_a_enviar.items():
        
        # Generamos el texto (Paso 3 del Flujo)
        conteo = len(designaciones_set)
        plural = "s" if conteo > 1 else ""
        titulo = "Vencimiento de Designaciones"
        mensaje = (
            f"Hay {conteo} designacion{plural} de tu carrera próxima{plural} "
            f"a vencer en los próximos 30 días. Revísalas aquí."
        )

        # Paso 4 del Flujo
        # Creamos la Notificación (el contenido)
        notif_obj, _ = models.Notificacion.objects.get_or_create(
            titulo=titulo,
            mensaje=mensaje,
            tipo="ALERTA"
        )

        # Creamos la UsuarioNotificacion (la asignación al coordinador)
        # Asumimos que el coordinador tiene un campo 'usuario' (OneToOne)
        un, created = models.UsuarioNotificacion.objects.get_or_create(
            usuario=coordinador.usuario,
            notificacion=notif_obj
        )

        # Esta es la lógica clave para manejar las reiteraciones y descartes
        if created:
            # Es nueva, el coordinador la verá.
            print(f"Nueva notificación creada para {coordinador.usuario.username}")
        elif un.leida or un.eliminado:
            # El coordinador ya la leyó o descartó, no lo molestamos.
            # (Paso 7 - Marcar como revisada)
            continue
        else:
            # La notificación ya existe pero no fue leída/descartada.
            # "Reiteramos" la notificación asegurándonos de que sea visible.
            # (Esto cumple con "se reitera semanalmente")
            un.leida = False
            un.eliminado = False
            un.save()
            print(f"Notificación reactivada para {coordinador.usuario.username}")

    print(f"Tarea 'notificar_vencimientos_designaciones' completada.")