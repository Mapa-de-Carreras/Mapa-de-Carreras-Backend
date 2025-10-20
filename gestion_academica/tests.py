from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from gestion_academica.models import *


# --- ESTRUCTURA ACADÉMICA ---

class InstitutoCarreraTests(TestCase):
    """
    Prueba la creación básica de un Instituto y una Carrera, 
    y verifica que la relación entre ellos sea correcta.
    """

    def test_crear_instituto_y_carrera(self):
        instituto = Instituto.objects.create(
            codigo="IDEI", nombre="Instituto de Informática")
        carrera = Carrera.objects.create(
            codigo="INF-GRADO", nombre="Ingeniería en Informática",
            nivel="GRADO", instituto=instituto
        )
        self.assertEqual(str(carrera), "Ingeniería en Informática")
        self.assertEqual(carrera.instituto, instituto)


class ResolucionPlanAsignaturaTests(TestCase):
    # Preparamos los datos base para las pruebas de la estructura académica
    def setUp(self):
        self.instituto = Instituto.objects.create(
            codigo="IDEI", nombre="Informática")
        self.carrera = Carrera.objects.create(
            codigo="INF-GRADO", nombre="Ing. Informática", nivel="GRADO", instituto=self.instituto)
        self.resolucion = Resolucion.objects.create(
            tipo="CS", emisor="UNIV", numero=123, anio=2024)

        # Asignaturas para pruebas de correlatividad
        self.asig1 = Asignatura.objects.create(
            codigo="ALG1", nombre="Algoritmos I", cuatrimestre=1,
            tipo_asignatura="OBLIGATORIA", tipo_duracion="CUATRIMESTRAL",
            horas_teoria=40, horas_practica=20)
        self.asig2 = Asignatura.objects.create(
            codigo="ALG2", nombre="Algoritmos II", cuatrimestre=2,
            tipo_asignatura="OBLIGATORIA", tipo_duracion="CUATRIMESTRAL",
            horas_teoria=40, horas_practica=20)
        self.asig3 = Asignatura.objects.create(
            codigo="FIS1", nombre="Física I", cuatrimestre=1,
            tipo_asignatura="OBLIGATORIA", tipo_duracion="CUATRIMESTRAL",
            horas_teoria=30, horas_practica=30)

    def test_horas_totales_calculadas(self):
        """Verifica que el método save() de Asignatura calcule las horas totales automáticamente."""
        self.assertEqual(self.asig1.horas_totales, 60)

    def test_plan_estudio_y_asignaturas(self):
        """Prueba la relación muchos-a-muchos entre PlanDeEstudio y Asignatura."""
        plan = PlanDeEstudio.objects.create(
            carrera=self.carrera, resolucion=self.resolucion, fecha_inicio="2024-01-01")
        pa1 = PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=self.asig1, anio=1)
        pa2 = PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=self.asig2, anio=1)
        self.assertEqual(plan.asignaturas.count(), 2)
        self.assertIn(self.asig1, plan.asignaturas.all())
        self.assertEqual(str(pa1), f"{plan} - {self.asig1} (año {pa1.anio})")

    def test_correlativa_valida(self):
        """Prueba que se puede crear una correlativa válida entre asignaturas de distintos períodos."""
        plan = PlanDeEstudio.objects.create(
            carrera=self.carrera, resolucion=self.resolucion, fecha_inicio="2024-01-01")
        pa1 = PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=self.asig1, anio=1)
        pa2 = PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=self.asig2, anio=2)
        correlativa = Correlativa(
            plan_asignatura=pa2, correlativa_requerida=pa1)
        correlativa.clean()
        correlativa.save()
        self.assertIn(correlativa, Correlativa.objects.all())

    def test_correlativa_invalida_misma_asignatura(self):
        """Prueba que una asignatura no puede ser correlativa de sí misma."""
        plan = PlanDeEstudio.objects.create(
            carrera=self.carrera, resolucion=self.resolucion, fecha_inicio="2024-01-01")
        pa1 = PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=self.asig1, anio=1)

        correlativa_invalida = Correlativa(
            plan_asignatura=pa1, correlativa_requerida=pa1)

        with self.assertRaises(ValidationError):
            correlativa_invalida.full_clean()

    def test_correlativa_invalida_mismo_periodo(self):
        """Prueba que el modelo rechaza correlativas en el mismo año y cuatrimestre."""
        plan = PlanDeEstudio.objects.create(
            carrera=self.carrera, resolucion=self.resolucion, fecha_inicio="2024-01-01")

        pa1 = PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=self.asig1, anio=1)
        pa3 = PlanAsignatura.objects.create(
            plan_de_estudio=plan, asignatura=self.asig3, anio=1)

        correlativa_invalida = Correlativa(
            plan_asignatura=pa1,
            correlativa_requerida=pa3
        )

        with self.assertRaises(ValidationError):
            correlativa_invalida.full_clean()


class ComisionTests(TestCase):
    def test_crear_comision(self):
        """Verifica la creación de una Comisión y su relación con Asignatura."""
        asignatura = Asignatura.objects.create(
            codigo="ALG1", nombre="Algoritmos I", tipo_asignatura="OBLIGATORIA",
            tipo_duracion="ANUAL", horas_teoria=20, horas_practica=10
        )
        comision = Comision.objects.create(
            nombre="Comisión A", turno="MATUTINO", asignatura=asignatura)
        self.assertEqual(str(comision), "Algoritmos I - Comisión A")


# --- USUARIOS Y ROLES ---

class UsuarioRolesTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            legajo="100", nombre="Juan", apellido="Pérez", email="jp@example.com", password="1234"
        )
        self.rol_docente = Rol.objects.create(nombre="Docente")

    def test_crear_usuario_y_rol(self):
        """Prueba la creación de un Usuario personalizado y la asignación de un Rol."""
        RolUsuario.objects.create(usuario=self.usuario, rol=self.rol_docente)
        self.assertIn(self.rol_docente, self.usuario.roles.all())
        self.assertEqual(str(self.usuario), "Pérez Juan")


class NotificacionesTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            legajo="200", nombre="Ana", apellido="Gomez", email="ana@example.com", password="1234"
        )
        self.notificacion = Notificacion.objects.create(
            titulo="Prueba", mensaje="Mensaje de prueba", tipo="INFO", creado_por=self.usuario)

    def test_crear_y_marcar_notificacion_leida(self):
        """Prueba el sistema de notificaciones, incluyendo su creación y el método para marcarla como leída."""
        un = UsuarioNotificacion.objects.create(
            usuario=self.usuario, notificacion=self.notificacion)
        self.assertFalse(un.leida)
        un.marcar_leida()
        self.assertTrue(un.leida)
        self.assertIsNotNone(un.fecha_leida)
        self.assertEqual(str(self.notificacion), "Prueba (" +
                         str(self.notificacion.fecha_creacion.date()) + ")")


# --- DOCENTES Y COORDINADORES ---

class DocenteCoordinadorTests(TestCase):
    def setUp(self):
        self.mod = Modalidad.objects.create(nombre="Presencial")
        self.carac = Caracter.objects.create(nombre="Regular")
        self.dedic = Dedicacion.objects.create(nombre="Simple")
        self.docente = Docente.objects.create_user(
            legajo="300", nombre="Luis", apellido="Lopez", email="ll@example.com", password="1234",
            modalidad=self.mod, caracter=self.carac, dedicacion=self.dedic
        )
        self.coord = Coordinador.objects.create_user(
            legajo="400", nombre="Sofía", apellido="Torres", email="st@example.com", password="1234"
        )
        self.instituto = Instituto.objects.create(
            codigo="IDEI", nombre="Informática")
        self.carrera = Carrera.objects.create(
            codigo="INF-GRADO", nombre="Ing. Informática", nivel="GRADO", instituto=self.instituto)

    def test_docente_y_coordinador(self):
        """Verifica que el __str__ de Docente y Coordinador use el formato 'Apellido, Nombre'."""
        self.assertEqual(str(self.docente), "Lopez Luis")
        self.assertEqual(str(self.coord), "Torres Sofía")

    def test_carrera_coordinacion(self):
        """Prueba que un Coordinador puede ser asignado a una Carrera a través del modelo 'puente'."""
        cc = CarreraCoordinacion.objects.create(
            carrera=self.carrera, coordinador=self.coord)
        self.assertTrue(cc.activo)
        self.assertIn(self.coord, self.carrera.coordinadores.all())


# --- DESIGNACIONES Y REGLAS ---

class DesignacionTests(TestCase):
    def setUp(self):
        self.modalidad = Modalidad.objects.create(nombre="Presencial")
        self.dedicacion = Dedicacion.objects.create(nombre="Simple")
        self.cargo = Cargo.objects.create(nombre="Titular")
        self.param = ParametrosRegimen.objects.create(
            modalidad=self.modalidad, dedicacion=self.dedicacion,
            horas_max_frente_alumnos=10, horas_min_frente_alumnos=5,
            horas_max_actual=12, horas_min_actual=6, max_asignaturas=2
        )
        self.docente = Docente.objects.create_user(
            legajo="500", nombre="Carlos", apellido="Diaz", email="cd@example.com", password="1234",
            modalidad=self.modalidad, dedicacion=self.dedicacion
        )
        asig1 = Asignatura.objects.create(
            codigo="BD1", nombre="Bases de Datos", tipo_asignatura="OBLIGATORIA", tipo_duracion="CUATRIMESTRAL")
        self.comision1 = Comision.objects.create(
            nombre="Comisión A", turno="VESPERTINO", asignatura=asig1)

        asig2 = Asignatura.objects.create(
            codigo="ARQ1", nombre="Arquitectura", tipo_asignatura="OBLIGATORIA", tipo_duracion="CUATRIMESTRAL")
        self.comision2 = Comision.objects.create(
            nombre="Comisión B", turno="MATUTINO", asignatura=asig2)

    def test_crear_designacion(self):
        """Prueba la creación exitosa de una Designación."""
        designacion = Designacion.objects.create(
            fecha_inicio="2024-03-01", tipo_designacion="TEORICO",
            docente=self.docente, comision=self.comision1, regimen=self.param, cargo=self.cargo
        )
        self.assertEqual(str(designacion),
                         f"{self.docente} en {self.comision1}")
        self.assertEqual(self.docente.designaciones.count(), 1)

    def test_impide_exceder_maximo_asignaturas(self):
        """Prueba que el modelo rechaza una designación si el docente excede su límite."""
        # 1. Creamos la primera designación (válida, 1 de 2)
        Designacion.objects.create(
            docente=self.docente, comision=self.comision1, regimen=self.param,
            cargo=self.cargo, fecha_inicio="2024-03-01"
        )

        # 2. Creamos la segunda designación (válida, 2 de 2)
        Designacion.objects.create(
            docente=self.docente, comision=self.comision2, regimen=self.param,
            cargo=self.cargo, fecha_inicio="2024-08-01"
        )

        # 3. Creamos una tercera asignatura y comisión para el intento inválido
        asig3 = Asignatura.objects.create(
            codigo="SO1", nombre="Sist. Operativos")
        comision3 = Comision.objects.create(
            nombre="Com C", asignatura=asig3, turno="NOCHE")

        # 4. Intentamos crear la tercera designación (inválida, 3 de 2)
        designacion_invalida = Designacion(
            docente=self.docente, comision=comision3, regimen=self.param,
            cargo=self.cargo, fecha_inicio="2025-03-01"
        )

        # 5. Verificamos que el método clean() lance el error esperado
        with self.assertRaises(ValidationError):
            designacion_invalida.full_clean()


class TestParametrosRegimenValidation(TestCase):
    def setUp(self):
        self.modalidad = Modalidad.objects.create(nombre="Presencial")
        self.dedicacion_simple = Dedicacion.objects.create(nombre="Simple")
        self.dedicacion_exclusiva = Dedicacion.objects.create(
            nombre="Exclusiva")

    def test_max_asignaturas_valido_para_dedicacion_simple(self):
        """Prueba que un régimen con dedicación simple y max_asignaturas=2 es válido."""
        regimen = ParametrosRegimen(
            modalidad=self.modalidad,
            dedicacion=self.dedicacion_simple,
            max_asignaturas=2,
            horas_max_frente_alumnos=10, horas_min_frente_alumnos=5,
            horas_max_actual=12, horas_min_actual=6
        )
        regimen.full_clean()  # No debería lanzar un error

    def test_max_asignaturas_invalido_para_dedicacion_simple(self):
        """Prueba que el modelo rechaza un régimen con dedicación simple y max_asignaturas > 2."""
        regimen_invalido = ParametrosRegimen(
            modalidad=self.modalidad,
            dedicacion=self.dedicacion_simple,
            max_asignaturas=3,  # Esto es inválido
            horas_max_frente_alumnos=10, horas_min_frente_alumnos=5,
            horas_max_actual=12, horas_min_actual=6
        )
        with self.assertRaises(ValidationError):
            regimen_invalido.full_clean()
