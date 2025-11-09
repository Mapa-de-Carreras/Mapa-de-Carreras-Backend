# gestion_academica/tests/test_serializers.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from gestion_academica import models

from gestion_academica.serializers.gestion_academica_serializer import *

from gestion_academica.serializers.M2_gestion_docentes import (
    CaracterSerializer, ModalidadSerializer, DedicacionSerializer,
    ParametrosRegimenSerializer, DocenteSerializer
)
from gestion_academica.serializers.M3_designaciones_docentes import (
    ComisionSerializer, CargoSerializer, DesignacionSerializer
)
from gestion_academica.serializers.M4_gestion_usuarios_autenticacion import (
    UsuarioSerializer, NotificacionSerializer, UsuarioNotificacionSerializer,
    CarreraCoordinacionSerializer, CoordinadorSerializer, RolSerializer, RolUsuarioSerializer
)


User = get_user_model()


class SerializersIntegrationTests(TestCase):
    def setUp(self):
        # crear catálogos con get_or_create para evitar duplicados
        self.instituto, _ = models.Instituto.objects.get_or_create(
            codigo="IDEI", nombre="Informática")
        self.carrera, _ = models.Carrera.objects.get_or_create(
            codigo="INF-GRADO", nombre="Ing. Informática", nivel="GRADO", instituto=self.instituto)
        self.documento, _ = models.Documento.objects.get_or_create(
            tipo="CS", emisor="UNIV", numero=123, anio=2024)

        # catálogos docentes
        self.modalidad, _ = models.Modalidad.objects.get_or_create(
            nombre="Presencial")
        self.caracter, _ = models.Caracter.objects.get_or_create(
            nombre="Regular")
        self.dedicacion, _ = models.Dedicacion.objects.get_or_create(
            nombre="Simple")

        # ParametrosRegimen
        self.param = models.ParametrosRegimen.objects.create(
            modalidad=self.modalidad,
            dedicacion=self.dedicacion,
            horas_max_frente_alumnos=10,
            horas_min_frente_alumnos=5,
            horas_max_actual=12,
            horas_min_actual=6,
            max_asignaturas=2
        )

        # Usuario base
        self.usuario_payload = {
            "legajo": "U100",
            "nombre": "User",
            "apellido": "Test",
            "email": "user.test@example.com",
            "password": "pass1234"
        }

    def test_instituto_carrera_serializers(self):
        s = InstitutoSerializer(data={"codigo": "INS1", "nombre": "Inst 1"})
        self.assertTrue(s.is_valid(), s.errors)
        inst = s.save()
        self.assertEqual(inst.codigo, "INS1")

        cs = CarreraSerializerList(
            data={"codigo": "C1", "nombre": "Carrera 1", "nivel": "GRADO", "instituto_id": inst.id})
        self.assertTrue(cs.is_valid(), cs.errors)
        carrera = cs.save()
        self.assertEqual(carrera.instituto.id, inst.id)

    def test_asignatura_plan_documento(self):
        # Asignatura (horas_totales calculadas)
        a_payload = {
            "codigo": "ALG1",
            "nombre": "Algoritmos I",
            "cuatrimestre": 1,
            "tipo_asignatura": "OBLIGATORIA",
            "tipo_duracion": "CUATRIMESTRAL",
            "horas_teoria": 40,
            "horas_practica": 20,
        }
        s_asig = AsignaturaSerializer(data=a_payload)
        self.assertTrue(s_asig.is_valid(), s_asig.errors)
        asig = s_asig.save()
        self.assertEqual(asig.horas_totales, 60)

        # Documento
        d_payload = {"tipo": "Mem", "emisor": "Decanatura",
                     "numero": "01", "anio": 2024}
        s_doc = DocumentoSerializer(data=d_payload)
        self.assertTrue(s_doc.is_valid(), s_doc.errors)
        doc = s_doc.save()
        self.assertEqual(doc.anio, 2024)

        # PlanDeEstudio con PlanAsignatura (crear plan, luego plan-asignatura)
        p_payload = {"fecha_inicio": "2024-01-01", "carrera_id": self.carrera.id, "documento_id": doc.id}
        s_plan = PlanDeEstudioSerializerDetail(data=p_payload)
        self.assertTrue(s_plan.is_valid(), s_plan.errors)
        plan = s_plan.save()

        pa_payload = {"plan_de_estudio": plan.id,
                      "asignatura_id": asig.id, "anio": 1}
        s_pa = PlanAsignaturaSerializer(data=pa_payload)
        self.assertTrue(s_pa.is_valid(), s_pa.errors)
        pa = s_pa.save()
        # ahora PlanDeEstudio.asignaturas debe contener la asignatura a través del through
        self.assertIn(asig, plan.asignaturas.all())

        # Correlativa válida
        # crear otra asignatura en cuatrimestre distinto
        a2 = models.Asignatura.objects.create(
            codigo="ALG2", nombre="Algoritmos II", cuatrimestre=2, tipo_asignatura="OBLIGATORIA", tipo_duracion="CUATRIMESTRAL")
        pa2 = models.PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=a2, anio=1)
        correl_payload = {"plan_asignatura": pa2.id,
                          "correlativa_requerida": pa.id}
        s_corr = CorrelativaSerializer(data=correl_payload)
        self.assertTrue(s_corr.is_valid(), s_corr.errors)
        corr = s_corr.save()
        self.assertEqual(corr.plan_asignatura.id, pa2.id)

    def test_usuario_docente_serializers_with_password(self):
        # Usuario create via UsuarioSerializer
        s_user = UsuarioSerializer(data=self.usuario_payload)
        self.assertTrue(s_user.is_valid(), s_user.errors)
        user = s_user.save()
        self.assertTrue(user.check_password(self.usuario_payload["password"]))

        # Crear Docente vía serializer (con password). Se usa legajo distinct para evitar conflicto.
        docente_payload = {
            "legajo": "DOC1",
            "nombre": "Doc",
            "apellido": "One",
            "email": "doc.one@example.com",
            "modalidad_id": self.modalidad.id,
            "caracter_id": self.caracter.id,
            "dedicacion_id": self.dedicacion.id,
            "password": "docpass"
        }
        s_docente = DocenteSerializer(data=docente_payload)
        self.assertTrue(s_docente.is_valid(), s_docente.errors)
        docente = s_docente.save()
        # docente debe tener contraseña usable
        self.assertTrue(docente.check_password("docpass"))
        self.assertEqual(docente.modalidad.id, self.modalidad.id)

        # Update docente (partial)
        s_docente_upd = DocenteSerializer(
            docente, data={"celular": "12345"}, partial=True)
        self.assertTrue(s_docente_upd.is_valid(), s_docente_upd.errors)
        docente_updated = s_docente_upd.save()
        self.assertEqual(docente_updated.celular, "12345")

    def test_parametros_regimen_and_designacion(self):
        # Cargo
        cargo = models.Cargo.objects.create(nombre="Titular")
        # asignaturas y comisiones
        asig1 = models.Asignatura.objects.create(
            codigo="BD1", nombre="Bases de Datos", tipo_asignatura="OBLIGATORIA", tipo_duracion="CUATRIMESTRAL")
        com1 = models.Comision.objects.create(
            nombre="Com A", turno="MATUTINO", asignatura=asig1)
        # crear docente con create_user fallback si es necesario
        docente = models.Docente.objects.create_user(
            legajo="DOC2", nombre="Doc2", apellido="Apellido", email="doc2@example.com", password="p")
        # designacion crea y valida límite en clean()
        d_payload = {
            "fecha_inicio": "2024-03-01",
            "tipo_designacion": "TEORICO",
            "docente": docente.id,
            "comision": com1.id,
            "regimen": self.param.id,
            "cargo": cargo.id
        }
        s_design = DesignacionSerializer(data=d_payload)
        self.assertTrue(s_design.is_valid(), s_design.errors)
        design = s_design.save()
        self.assertEqual(design.docente.id, docente.id)

    def test_notificacion_and_carrera_coordinacion(self):
        # crear creador
        creador = models.Usuario.objects.create_user(
            legajo="U200", nombre="Creador", apellido="X", email="c@example.com", password="p")
        # Notificacion
        notif_payload = {"titulo": "T1", "mensaje": "Hola",
                         "tipo": "INFO", "creado_por_id": creador.id}
        s_not = NotificacionSerializer(data=notif_payload)
        self.assertTrue(s_not.is_valid(), s_not.errors)
        noti = s_not.save()
        # UsuarioNotificacion
        un = models.UsuarioNotificacion.objects.create(
            usuario=creador, notificacion=noti)
        self.assertFalse(un.leida)
        un.marcar_leida()
        self.assertTrue(un.leida)

        # CarreraCoordinacion + CoordinadorSerializer
        coord = models.Coordinador.objects.create_user(
            legajo="COORD1", nombre="Coord", apellido="C", email="coord@example.com", password="p")
        cc_payload = {"carrera_id": self.carrera.id,
                      "coordinador_id": coord.id, "creado_por_id": creador.id}
        s_cc = CarreraCoordinacionSerializer(data=cc_payload)
        self.assertTrue(s_cc.is_valid(), s_cc.errors)
        cc = s_cc.save()
        self.assertTrue(cc.activo)
        # CoordinadorSerializer read-only nested list present
        s_coord = CoordinadorSerializer(coord)
        self.assertIn('carreras_coordinadas', s_coord.data)