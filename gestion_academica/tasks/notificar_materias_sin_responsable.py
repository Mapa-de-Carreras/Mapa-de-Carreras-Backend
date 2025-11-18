from django.utils import timezone
from gestion_academica import models
from django.db.models import Q

# --- NOTIFICAR MATERIAS SIN RESPONSABLE ---

def notificar_materias_sin_responsable():
    """
    Busca asignaturas en planes vigentes que no tengan designaciones
    activas y notifica a los coordinadores correspondientes.
   
    """
    print(f"[{timezone.now()}] Ejecutando tarea: notificar_materias_sin_responsable...")
    hoy = timezone.now()

    # Paso 2: Consultar asignaturas del plan de estudio vigente
    #
    # Filtramos por Asignaturas que estén activas Y en un plan vigente
    asignaturas_en_planes_vigentes = models.Asignatura.objects.filter(
        activo=True,
        planes_de_estudio__esta_vigente=True,
        planes_de_estudio__carrera__isnull=False # Aseguramos que el plan tenga carrera
    ).distinct()

    # Paso 3: Identificar las que NO tienen designaciones activas
    #
    # Una "designación activa" es una que no tiene fecha_fin
    # o cuya fecha_fin es en el futuro. Usaremos fecha_fin__isnull=True
    # para simplificar (o puedes usar Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=hoy))
    
    # Optenemos los IDs de las asignaturas que SÍ tienen responsable
    asignaturas_con_responsable_ids = models.Designacion.objects.filter(
        Q(fecha_fin__isnull=True) | # (A) Es permanente
        Q(fecha_fin__gt=hoy)        # (B) O vence en el futuro (gt='greather than')
    ).values_list('comision__asignatura__pk', flat=True).distinct()

    # Excluimos para encontrar las que NO tienen responsable
    asignaturas_sin_responsable = asignaturas_en_planes_vigentes.exclude(
        pk__in=asignaturas_con_responsable_ids
    ).prefetch_related(
        'planes_de_estudio__carrera'
    )

    if not asignaturas_sin_responsable.exists():
        # Flujo secundario: "Asignatura con responsable"
        print("No se encontraron materias sin responsable.")
        return

    # Paso 4: Agrupar por coordinador y carrera
    # {coordinador_obj: {carrera_obj: {asig1, asig2}, ...}}
    notificaciones_a_enviar = {}

    for asig in asignaturas_sin_responsable:
        # Obtenemos los planes vigentes de esta asignatura
        planes_vigentes = asig.planes_de_estudio.filter(esta_vigente=True)
        
        for plan in planes_vigentes:
            carrera = plan.carrera
            if not carrera:
                continue

            # Buscamos coordinadores activos para esta carrera
            coordinadores_activos = models.Coordinador.objects.filter(
                carreras_coordinadas=carrera,
                carreracoordinacion__carrera=carrera,
                carreracoordinacion__activo=True,
                activo=True
            ).distinct()

            for coord in coordinadores_activos:
                if coord not in notificaciones_a_enviar:
                    notificaciones_a_enviar[coord] = {}
                if carrera not in notificaciones_a_enviar[coord]:
                    notificaciones_a_enviar[coord][carrera] = set()
                
                notificaciones_a_enviar[coord][carrera].add(asig)

    # Paso 5: Registrar las notificaciones
    for coordinador, carreras_dict in notificaciones_a_enviar.items():
        for carrera, asignaturas_set in carreras_dict.items():
            
            conteo = len(asignaturas_set)
            plural = "s" if conteo > 1 else ""
            titulo = f"Materias sin Responsable ({carrera.nombre})"
            mensaje = (
                f"Se ha{plural} detectado {conteo} materia{plural} sin docente responsable "
                f"designado en el plan vigente de la carrera {carrera.nombre}. "
                "Revísalas aquí."
            )

            # Creamos la Notificación
            notif_obj, _ = models.Notificacion.objects.get_or_create(
                titulo=titulo,
                mensaje=mensaje,
                tipo="ADVERTENCIA"
            )

            # Creamos la UsuarioNotificacion (la asignación)
            un, created = models.UsuarioNotificacion.objects.get_or_create(
                usuario=coordinador.usuario,
                notificacion=notif_obj
            )

            # Manejamos las reiteraciones y recordatorios (Paso 7 y 8)
            if created:
                print(f"Notificación de materias sin responsable creada para {coordinador.usuario.username}")
            elif un.leida or un.eliminado:
                continue # El usuario ya la marcó como revisada
            elif un.fecha_recordatorio and un.fecha_recordatorio > hoy:
                continue # El usuario pidió "recordar más tarde"
            else:
                # Reactivamos la notificación para que se reitere
                un.leida = False
                un.eliminado = False
                un.fecha_recordatorio = None
                un.save()
                print(f"Notificación de materias sin responsable reactivada para {coordinador.usuario.username}")

    print(f"[{timezone.now()}] Tarea 'notificar_materias_sin_responsable' completada.")