# gestion_academica/serializers/M3_designaciones_docentes.py

from django.contrib.auth import get_user_model
from datetime import date, time, datetime, timezone
from django.utils import timezone as dj_timezone
from rest_framework import serializers
from gestion_academica import models
from gestion_academica.serializers.M2_gestion_docentes import DocenteSerializer
from django.db.models import Q

User = get_user_model()


class ComisionSerializer(serializers.ModelSerializer):
    asignatura_nombre = serializers.CharField(
        source="plan_asignatura_asignatura.nombre", read_only=True)

    class Meta:
        model = models.Comision
        fields = [
            "id", "nombre", "turno", "promocionable", "activo",
            "plan_asignatura", "asignatura_nombre"
        ]
        read_only_fields = ["id", "asignatura_nombre"]


class ComisionCreateUpdateSerializer(serializers.ModelSerializer):
    asignatura_id = serializers.PrimaryKeyRelatedField(
        source="asignatura", queryset=models.Asignatura.objects.all(), write_only=True
    )

    class Meta:
        model = models.Comision
        fields = ["nombre", "turno", "promocionable",
                  "activo", "asignatura_id"]

    def validate(self, data):
        asignatura = data.get("asignatura") or getattr(
            self.instance, "asignatura", None)
        nombre = data.get("nombre") or getattr(self.instance, "nombre", None)

        if models.Comision.objects.filter(
            asignatura=asignatura, nombre__iexact=nombre
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                f"Ya existe una comisión llamada '{nombre}' para esta asignatura."
            )
        return data


class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Cargo
        fields = ["id", "nombre", "created_at", "updated_at"]


class DesignacionSerializer(serializers.ModelSerializer):
    advertencia = serializers.CharField(read_only=True, help_text="Advertencia si el docente excede la carga horaria.")

    docente_id = serializers.PrimaryKeyRelatedField(
        source="docente",
        queryset=models.Docente.objects.all(),
        write_only=True,
        required=True
    )

    comision_id = serializers.PrimaryKeyRelatedField(
        source="comision",
        queryset=models.Comision.objects.filter(activo=True),
        write_only=True,
        required=True
    )

    cargo_id = serializers.PrimaryKeyRelatedField(
        source="cargo",
        queryset=models.Cargo.objects.all(),
        write_only=True,
        required=True
    )

    documento_id = serializers.PrimaryKeyRelatedField(
        source="documento",
        queryset=models.Documento.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    creado_por = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    dedicacion_id = serializers.PrimaryKeyRelatedField(
        source="dedicacion",
        write_only=True,
        queryset=models.Dedicacion.objects.all(),
        required=True
    )
    # ... (campos de solo lectura) ...
    docente = DocenteSerializer(read_only=True)
    comision = ComisionSerializer(read_only=True)
    cargo = CargoSerializer(read_only=True)
    activo = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.Designacion
        fields = [
            "id", "fecha_inicio", "fecha_fin", "tipo_designacion",
            "docente", "docente_id", "comision", "comision_id",
            "cargo", "cargo_id", "observacion", "documento", "documento_id",
            "dedicacion_id", "creado_por", "created_at",
            "updated_at", "activo",
            "advertencia"
        ]
        read_only_fields = ["creado_por", "created_at",
                            "updated_at",
                            "activo", "advertencia"]
        
    def _periodos_solapan(self, a_start, a_end, b_start, b_end):
        """
        Devuelve True si los intervalos se solapan.
        """
        def _to_aware_dt(value):
            if value is None:
                return datetime.max.replace(tzinfo=timezone.utc)
            if isinstance(value, datetime):
                if dj_timezone.is_naive(value):
                    return dj_timezone.make_aware(value, timezone=dj_timezone.get_current_timezone())
                return value
            if isinstance(value, date):
                dt = datetime.combine(value, time.min)
                return dj_timezone.make_aware(dt, timezone=dj_timezone.get_current_timezone())
            if isinstance(value, str):
                try:
                    s = value.replace("Z", "+00:00")
                    parsed = datetime.fromisoformat(s)
                    if dj_timezone.is_naive(parsed):
                        return dj_timezone.make_aware(parsed, timezone=dj_timezone.get_current_timezone())
                    return parsed
                except Exception:
                    return datetime.max.replace(tzinfo=timezone.utc)
            return datetime.max.replace(tzinfo=timezone.utc)

        a_start_dt = _to_aware_dt(a_start)
        a_end_dt = _to_aware_dt(a_end)
        b_start_dt = _to_aware_dt(b_start)
        b_end_dt = _to_aware_dt(b_end)
        return not (a_end_dt < b_start_dt or b_end_dt < a_start_dt)

    def validate(self, data):
        # Obtenemos los datos para la validación.
        # Si es un UPDATE, data solo tiene los campos que cambiaron.
        # Usamos 'self.instance' para obtener los campos que no cambiaron.
        instance = self.instance
        docente = data.get("docente", getattr(instance, "docente", None))
        comision = data.get("comision", getattr(instance, "comision", None))
        cargo = data.get("cargo", getattr(instance, "cargo", None))
        fecha_inicio = data.get("fecha_inicio", getattr(instance, "fecha_inicio", None))
        fecha_fin = data.get("fecha_fin", getattr(instance, "fecha_fin", None))
        documento = data.get("documento", getattr(instance, "documento", None))
        dedicacion = data.get("dedicacion", getattr(instance, "dedicacion", None))

        # --- Validación de Fechas ---
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise serializers.ValidationError({"fecha_fin": "La fecha de fin no puede ser anterior a la fecha de inicio."})

        # --- Validación de Cargo ---
        if cargo and cargo.nombre.lower() == "contratado" and documento is not None:
            raise serializers.ValidationError({"documento": "Las designaciones 'Contratado' no deben venir con documento."})

        # --- Validación de Solapamiento ---
        
        # 1. Solapamiento en misma comisión
        qs_misma_comision = models.Designacion.objects.filter(
            docente=docente, comision=comision, activo=True
        )
        if instance: # Si es update, excluimos esta misma designación
            qs_misma_comision = qs_misma_comision.exclude(pk=instance.pk)
        
        for d in qs_misma_comision:
            if self._periodos_solapan(d.fecha_inicio, d.fecha_fin, fecha_inicio, fecha_fin):
                raise serializers.ValidationError("Solapamiento detectado con otra designación en la misma comisión.")

        # --- Validación de Régimen ---
        #
        modalidad_obj = getattr(docente, "modalidad", None)

        if modalidad_obj is None:
            raise serializers.ValidationError("No se pudo determinar la modalidad: el docente debe tener modalidad asignada.")

        # Verificamos que exista un régimen. Si no existe, fallamos.
        try:
            models.ParametrosRegimen.objects.get(
                modalidad=modalidad_obj,
                dedicacion=dedicacion,
                activo=True
            )
        except models.ParametrosRegimen.DoesNotExist:
            raise serializers.ValidationError("No existe un parámetro de régimen activo para la modalidad del docente y la dedicación indicada.")

        return data
    
    def create(self, validated_data):
        # 1. Obtenemos el usuario que crea
        actor = self.context['request'].user
        validated_data['creado_por'] = actor
        
        # 2. Guardamos la designación
        instance = super().create(validated_data)
        
        # 3. Verificamos la carga horaria y generamos la advertencia/notificación
        self.advertencia_msg = self._verificar_carga_horaria_y_notificar(instance, actor)
        
        return instance

    def update(self, instance, validated_data):
        # 1. Obtenemos el usuario que edita
        actor = self.context['request'].user
        
        # 2. Guardamos los cambios
        instance = super().update(instance, validated_data)
        
        # 3. Verificamos la carga horaria y generamos la advertencia/notificación
        self.advertencia_msg = self._verificar_carga_horaria_y_notificar(instance, actor)
        
        return instance

    def _calcular_carga_total_docente(self, docente):
        """
        Calcula la carga horaria total de un docente
        sumando TODAS sus designaciones activas en la BD.
        """
        hoy = dj_timezone.now()
        
        # Busca todas las designaciones que están activas AHORA MISMO
        designaciones_activas = models.Designacion.objects.filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gt=hoy),
            docente=docente,
            activo=True
        ).select_related(
            'comision__plan_asignatura'
        )

        total_horas = 0
        
        # Suma las horas de todas las designaciones encontradas
        for desig in designaciones_activas:
            try:
                pa = desig.comision.plan_asignatura
                if desig.tipo_designacion == 'TEORICO':
                    total_horas += pa.horas_teoria
                elif desig.tipo_designacion == 'PRACTICO':
                    total_horas += pa.horas_practica
                elif desig.tipo_designacion == 'TEORICO + PRACTICO':
                    total_horas += pa.horas_totales
            except AttributeError:
                continue 
        
        return total_horas
    
    def _verificar_carga_horaria_y_notificar(self, designacion, actor):
        """
        Verifica el régimen, genera advertencia
        y crea la notificación si se excede el límite.
        """
        docente = designacion.docente
        
        # 1. Calcular carga total (incluye la designacion que acabamos de guardar)
        carga_total = self._calcular_carga_total_docente(docente)

        # 2. Verificar que el docente tenga modalidad
        if not docente.modalidad:
            return None 

        try:
            # 3. Buscar el régimen (usando la dedicacion de la designacion)
            regimen = models.ParametrosRegimen.objects.get(
                modalidad=docente.modalidad,
                dedicacion=designacion.dedicacion,
                activo=True
            )
            limite_horas = regimen.horas_max_frente_alumnos
        except models.ParametrosRegimen.DoesNotExist:
            return None # No hay régimen, no hay advertencia

        # 4. Comprobar el límite
        if carga_total <= limite_horas:
            return None 

        # 5. Generar advertencia (si 12 <= 10, etc.)
        advertencia_msg = (
            f"El docente {docente.usuario.__str__()} supera la carga "
            f"máxima permitida ({limite_horas}hs) según su régimen. "
            f"Carga total acumulada: {carga_total}hs."
        )

        # ... (lógica de notificación se queda igual) ...
        titulo = "Carga horaria excedida"
        mensaje = (
            f"Se guardó una designación para el docente {docente.usuario.__str__()} "
            f"que excede su carga horaria máxima permitida. "
            f"Carga actual: {carga_total}hs / Límite: {limite_horas}hs."
        )
        notif_obj, _ = models.Notificacion.objects.get_or_create(
            titulo=titulo, mensaje=mensaje, tipo="ADVERTENCIA", creado_por=actor
        )
        carreras_del_docente = models.Carrera.objects.filter(
            planes__planasignatura__comisiones__designaciones__docente=docente
        ).distinct()
        coordinadores_a_notificar = models.Coordinador.objects.filter(
            carreras_coordinadas__in=carreras_del_docente,
            carreracoordinacion__activo=True,
            activo=True
        ).distinct()
        for coord in coordinadores_a_notificar:
            models.UsuarioNotificacion.objects.get_or_create(
                usuario=coord.usuario, notificacion=notif_obj
            )
        return advertencia_msg
    
    def to_representation(self, instance):
        """
        Añade la advertencia (si existe) a la respuesta JSON.
        """
        data = super().to_representation(instance)
        
        # Si 'advertencia_msg' se guardó en el serializer
        # (durante create/update), lo añadimos a la respuesta
        if hasattr(self, 'advertencia_msg'):
            data['advertencia'] = self.advertencia_msg
        
        return data