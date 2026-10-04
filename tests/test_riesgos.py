# -*- coding: utf-8 -*-
import unittest

from db.memoria import BDMemoria
from riesgos.matriz import EvaluadorRiesgos


class TestPersistenciaRiesgos(unittest.TestCase):
    def test_riesgo_se_crea_edita_y_elimina_en_su_coleccion(self):
        db = BDMemoria()
        riesgo = {
            "modulo": "Control de acceso",
            "descripcion": "Decisión de acceso incorrecta",
            "mitigacion": "Revisión humana",
            "probabilidad_inicial": 3,
            "impacto_inicial": 4,
            "probabilidad_residual": 2,
            "impacto_residual": 2,
        }

        id_riesgo = db.insertar("riesgos_eticos", riesgo)
        guardado = db.obtener("riesgos_eticos", id_riesgo)
        self.assertEqual(guardado["modulo"], "Control de acceso")

        self.assertTrue(db.actualizar(
            "riesgos_eticos", id_riesgo, cambios={"impacto_inicial": 5}
        ))
        self.assertEqual(
            db.obtener("riesgos_eticos", id_riesgo)["impacto_inicial"], 5
        )

        self.assertTrue(db.eliminar("riesgos_eticos", id_riesgo))
        self.assertEqual(db.listar("riesgos_eticos"), [])


class TestEvaluadorRiesgos(unittest.TestCase):
    def setUp(self):
        self.evaluador = EvaluadorRiesgos()

    def test_calcula_puntajes_y_niveles_iniciales_y_residuales(self):
        procesado = self.evaluador.procesar_riesgo({
            "probabilidad_inicial": 4,
            "impacto_inicial": 5,
            "probabilidad_residual": 2,
            "impacto_residual": 3,
        })

        self.assertEqual(procesado["puntaje_inicial"], 20)
        self.assertEqual(procesado["nivel_inicial"], "Crítico")
        self.assertEqual(procesado["puntaje_residual"], 6)
        self.assertEqual(procesado["nivel_residual"], "Medio")

    def test_niveles_respetan_los_umbrales_configurados(self):
        self.assertEqual(self.evaluador.calcular_nivel(4), "Bajo")
        self.assertEqual(self.evaluador.calcular_nivel(5), "Medio")
        self.assertEqual(self.evaluador.calcular_nivel(10), "Alto")
        self.assertEqual(self.evaluador.calcular_nivel(17), "Crítico")

    def test_rechaza_probabilidad_o_impacto_fuera_de_escala(self):
        for valor in (0, 6, -1, "4", True, None):
            with self.subTest(valor=valor):
                with self.assertRaises(ValueError):
                    self.evaluador.procesar_riesgo({
                        "probabilidad_inicial": valor,
                        "impacto_inicial": 3,
                        "probabilidad_residual": 1,
                        "impacto_residual": 1,
                    })


if __name__ == "__main__":
    unittest.main()
