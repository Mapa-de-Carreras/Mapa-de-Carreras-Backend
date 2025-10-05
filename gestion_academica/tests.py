from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import *

# --- PRUEBAS DE ESTRUCTURA ACADÉMICA ---


class TestInstitutoModel(TestCase):
    def test_creacion_y_representacion_str(self):
        """Prueba que un Instituto se puede crear y su __str__ es correcto."""
        instituto = Instituto.objects.create(
            codigo="IDEI", nombre="Instituto de Desarrollo")
        self.assertEqual(str(instituto), "Instituto de Desarrollo")


class TestCarreraModel(TestCase):
    def setUp(self):
        self.instituto_idei = Instituto.objects.create(
            codigo="IDEI", nombre="Instituto de Desarrollo")

    def test_creacion_y_relacion_con_instituto(self):
        """Prueba que una Carrera se crea y se asocia correctamente a un Instituto."""
        carrera_ingenieria = Carrera.objects.create(
            codigo="ING-INF",
            nombre="Ingeniería en Informática",
            nivel="GRADO",
            instituto=self.instituto_idei
        )
        self.assertEqual(carrera_ingenieria.instituto, self.instituto_idei)


class TestAsignaturaModel(TestCase):
    def test_calculo_automatico_de_horas_totales(self):
        """Prueba que el método save() calcula horas_totales."""
        asignatura = Asignatura.objects.create(
            codigo="ALG1", nombre="Algoritmos I", anio=1, cuatrimestre=1,
            horas_teoria=40, horas_practica=20
        )
        self.assertEqual(asignatura.horas_totales, 60)


class TestCorrelativaModel(TestCase):
    def setUp(self):
        instituto = Instituto.objects.create(codigo="IDEI", nombre="Instituto")
        carrera = Carrera.objects.create(
            codigo="ING", nombre="Ingeniería", instituto=instituto)
        resolucion = Resolucion.objects.create(tipo="CS", numero=1, anio=2024)
        plan_2024 = PlanDeEstudio.objects.create(
            carrera=carrera, resolucion=resolucion, fecha_inicio='2024-01-01')

        asignatura_algoritmos_1 = Asignatura.objects.create(
            codigo="ALG1", nombre="Algoritmos I", anio=1, cuatrimestre=1)
        asignatura_algoritmos_2 = Asignatura.objects.create(
            codigo="ALG2", nombre="Algoritmos II", anio=1, cuatrimestre=2)

        self.plan_asignatura_alg1 = PlanAsignatura.objects.create(
            plan_de_estudio=plan_2024, asignatura=asignatura_algoritmos_1)
        self.plan_asignatura_alg2 = PlanAsignatura.objects.create(
            plan_de_estudio=plan_2024, asignatura=asignatura_algoritmos_2)

    def test_creacion_correlativa_valida(self):
        """Prueba que se puede crear una correlativa válida."""
        Correlativa.objects.create(
            plan_asignatura=self.plan_asignatura_alg2,
            correlativa_requerida=self.plan_asignatura_alg1
        )
        existe = Correlativa.objects.filter(
            plan_asignatura=self.plan_asignatura_alg2,
            correlativa_requerida=self.plan_asignatura_alg1
        ).exists()
        self.assertTrue(existe, "La correlativa válida no se pudo encontrar.")

# --- PRUEBAS DE PERSONAL Y ROLES ---


class TestPerfilesDeUsuario(TestCase):
    def test_usuario_puede_ser_docente_y_coordinador(self):
        """Prueba que un User puede tener ambos perfiles a la vez."""
        usuario_ana = User.objects.create_user(
            username='anagomez', first_name='Ana', last_name='Gomez')
        Docente.objects.create(user=usuario_ana, legajo='12345')
        Coordinador.objects.create(user=usuario_ana)

        self.assertTrue(hasattr(usuario_ana, 'docente'))
        self.assertTrue(hasattr(usuario_ana, 'coordinador'))

# --- PRUEBAS DE EVENTOS ---


class TestDesignacionModel(TestCase):
    def setUp(self):
        usuario_docente = User.objects.create_user(
            username='jperez', first_name='Juan')
        cargo_titular = Cargo.objects.create(nombre='Titular')
        modalidad_presencial = Modalidad.objects.create(nombre='Presencial')
        self.docente_juan = Docente.objects.create(
            user=usuario_docente, legajo='1001', cargo=cargo_titular, modalidad=modalidad_presencial)

        instituto = Instituto.objects.create(codigo="IDEI", nombre="Instituto")
        carrera = Carrera.objects.create(
            codigo="ING", nombre="Ingeniería", instituto=instituto)
        asignatura = Asignatura.objects.create(
            codigo="ALG1", nombre="Algoritmos I", anio=1, cuatrimestre=1)
        self.comision_algoritmos = Comision.objects.create(
            nombre='Comisión A', asignatura=asignatura, turno='TARDE')

        dedicacion_simple = Dedicacion.objects.create(nombre='Simple')
        self.regimen_simple = ParametrosRegimen.objects.create(
            modalidad=modalidad_presencial, dedicacion=dedicacion_simple, max_asignaturas=2, horas_max_semanal=10, horas_min_semanal=5, horas_max_anual=200, horas_min_anual=100)

    def test_creacion_designacion_y_relaciones(self):
        """Prueba que una Designacion se crea y conecta correctamente."""
        designacion = Designacion.objects.create(
            fecha_inicio='2024-03-01',
            docente=self.docente_juan,
            comision=self.comision_algoritmos,
            regimen=self.regimen_simple
        )
        self.assertEqual(designacion.docente.legajo, '1001')
        self.assertEqual(self.docente_juan.designaciones.count(), 1)
