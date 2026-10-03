# -*- coding: utf-8 -*-
import unittest

from reglas import (REGLAS, SEMAFORO, analizar_reglas, certificacion_vigente, evaluar_camion, evaluar_reglas,
                    horario_restringido, tabla_verdad_completa, tabla_verdad_regla, texto_peas, texto_tablas_verdad)


class TestReglas(unittest.TestCase):
    ESPERADO = {
        (1, 1, 1, 1): (0, 1), (1, 1, 1, 0): (0, 1), (1, 1, 0, 1): (0, 1), (1, 1, 0, 0): (0, 1),
        (1, 0, 1, 1): (1, 1), (1, 0, 1, 0): (0, 1), (1, 0, 0, 1): (1, 0), (1, 0, 0, 0): (0, 0),
        (0, 1, 1, 1): (0, 0), (0, 1, 1, 0): (0, 0), (0, 1, 0, 1): (0, 0), (0, 1, 0, 0): (0, 0),
        (0, 0, 1, 1): (0, 0), (0, 0, 1, 0): (0, 0), (0, 0, 0, 1): (0, 0), (0, 0, 0, 0): (0, 0)}

    def test_reglas_originales_a_mano(self):
        for (p, q, r, s), (a, e) in self.ESPERADO.items():
            res = evaluar_camion(bool(p), bool(q), bool(r), bool(s))
            self.assertEqual((res["acceso_estandar"], res["inspeccion_especial"]), (bool(a), bool(e)))

    def test_tablas_de_las_reglas_nuevas(self):
        self.assertEqual({(f["R"], f["H"]): f["D"] for f in tabla_verdad_regla("D")},
                         {(True, True): True, (True, False): False, (False, True): False, (False, False): False})
        self.assertEqual({(f["P"], f["S"]): f["B"] for f in tabla_verdad_regla("B")},
                         {(True, True): False, (True, False): True, (False, True): False, (False, False): False})
        self.assertEqual(len(tabla_verdad_completa()), 32)

    def test_decisiones_y_prioridad(self):
        casos = [((True, False, False, True, False), "ACCESO_ESTANDAR"), ((True, True, False, True, False), "INSPECCION_ESPECIAL"),
                 ((True, False, True, True, False), "INSPECCION_ESPECIAL"), ((False, False, False, True, False), "DENEGADO"),
                 ((True, False, True, True, True), "DENEGADO"),      # D gana a E y A
                 ((True, False, False, False, False), "DENEGADO"),   # B
                 ((True, True, False, False, False), "DENEGADO")]    # B gana a E
        for (P, Q, R, S, H), esperado in casos:
            self.assertEqual(evaluar_reglas(P, Q, R, S, H)["decision"], esperado, (P, Q, R, S, H))

    def test_todas_las_combinaciones_tienen_decision_y_explicacion(self):
        for f in tabla_verdad_completa():
            res = evaluar_reglas(f["P"], f["Q"], f["R"], f["S"], f["H"])
            self.assertIn(res["decision"], SEMAFORO)
            self.assertTrue(res["explicacion"][-1].startswith("RESULTADO"))
        self.assertIn("COBERTURA: todas", analizar_reglas()[-1])

    def test_validacion_de_tipos(self):
        with self.assertRaises(TypeError):
            evaluar_reglas(1, False, False, True)

    def test_horario_y_certificacion(self):
        self.assertTrue(horario_restringido(23, 22, 6) and horario_restringido(3, 22, 6))
        self.assertFalse(horario_restringido(12, 22, 6))
        self.assertTrue(certificacion_vigente("2099-01-01"))
        self.assertFalse(certificacion_vigente("2000-01-01") or certificacion_vigente("basura"))

    def test_la_decision_coincide_con_la_tabla_de_verdad_y_el_semaforo(self):
        for f in tabla_verdad_completa():
            res = evaluar_reglas(f["P"], f["Q"], f["R"], f["S"], f["H"])
            self.assertEqual((res["A"], res["E"], res["D"], res["B"]), (f["A"], f["E"], f["D"], f["B"]))
            self.assertEqual(res["semaforo"], SEMAFORO[res["decision"]])

    def test_a_y_b_son_excluyentes_y_d_puede_coincidir_con_a(self):
        informe = " ".join(analizar_reglas())
        self.assertIn("EXCLUYENTES: A y B", informe)
        self.assertIn("CONCURRENTES: A y D", informe)

    def test_textos_para_mostrar_y_reportar(self):
        texto = texto_tablas_verdad()
        for regla in REGLAS:
            self.assertIn(f"{regla} = {REGLAS[regla]['formula']}", texto)
        self.assertIn("TABLA COMPLETA", texto)
        self.assertIn("P (Medidas de desempeño)", texto_peas())


if __name__ == "__main__":
    unittest.main()