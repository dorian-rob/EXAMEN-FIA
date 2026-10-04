# -*- coding: utf-8 -*-
import unittest
from datetime import datetime, timedelta

from config import CONFIG_DEFECTO
from db import BD, BDMemoria, ErrorBD, construir_doc_acceso, construir_doc_incidente
from utils import ahora


class TestBDMemoria(unittest.TestCase):
    def setUp(self):
        self.db = BDMemoria()

    def test_crud(self):
        id_ = self.db.insertar("camiones", {"placa": "AAA-111-A", "camion_id": "CAM-1"})
        self.assertEqual(self.db.obtener("camiones", id_)["placa"], "AAA-111-A")
        self.assertTrue(self.db.actualizar("camiones", id_, {"empresa": "X"}))
        self.assertEqual(self.db.obtener("camiones", id_)["empresa"], "X")
        self.assertTrue(self.db.eliminar("camiones", id_))
        self.assertIsNone(self.db.obtener("camiones", id_))
        self.assertFalse(self.db.eliminar("camiones", id_))

    def test_filtros_orden_y_limite(self):
        for n in (3, 1, 2):
            self.db.insertar("accesos", {"n": n, "decision": "DENEGADO" if n > 1 else "OK", "anidado": {"x": n}})
        self.assertEqual(self.db.contar("accesos", {"decision": "DENEGADO"}), 2)
        self.assertEqual(self.db.contar("accesos", {"n": {"$gte": 2}}), 2)
        self.assertEqual(self.db.contar("accesos", {"anidado.x": 1}), 1)
        self.assertEqual([d["n"] for d in self.db.listar("accesos", None, [("n", -1)], 2)], [3, 2])

    def test_actualizar_con_push_agrega_al_historial(self):
        id_ = self.db.insertar("incidentes", {"historial": []})
        self.db.actualizar("incidentes", id_, {"estado": "cerrado"}, {"historial": {"evento": "x"}})
        doc = self.db.obtener("incidentes", id_)
        self.assertEqual((doc["estado"], len(doc["historial"])), ("cerrado", 1))

    def test_agregacion_incidentes_por_categoria_y_semana(self):
        base = ahora()
        for dias, cat in ((0, "sobrepeso"), (0, "sobrepeso"), (0, "falla_software"), (14, "sobrepeso")):
            self.db.insertar("incidentes", {"fecha": base - timedelta(days=dias), "clasificacion": {"categoria": cat}})
        filas = self.db.incidentes_por_categoria_semana()
        self.assertEqual(sum(f["total"] for f in filas), 4)
        self.assertEqual(max(f["total"] for f in filas), 2)
        self.assertEqual(self.db.incidentes_por_categoria_semana(base + timedelta(days=1)), [])


class TestBDSinConexion(unittest.TestCase):
    def test_sin_conexion_lanza_error_amigable(self):
        db = BD(dict(CONFIG_DEFECTO))                 # nunca se llamó a conectar()
        self.assertFalse(db.conectado)
        with self.assertRaises(ErrorBD) as cm:
            db.listar("camiones")
        self.assertIn("Configuración", str(cm.exception))

    def test_conexion_fallida_guarda_el_motivo(self):
        db = BD({**CONFIG_DEFECTO, "mongo_uri": "mongodb://127.0.0.1:1/?serverSelectionTimeoutMS=300"})
        self.assertFalse(db.conectar())
        self.assertTrue(db.error)
        self.assertIsNone(db.cliente)
        self.assertIsNone(db.db)

    def test_agregacion_usa_fecha_escalar_y_tolera_resultado_incompleto(self):
        class ColeccionIncidentes:
            pipeline = None

            def aggregate(self, pipeline):
                self.pipeline = pipeline
                return [{
                    "_id": {"anio": None, "semana": None, "categoria": "Derrame"},
                    "total": 1,
                }]

        class BaseFalsa:
            def __init__(self):
                self.incidentes = ColeccionIncidentes()

            def __getitem__(self, nombre):
                if nombre != "incidentes":
                    raise KeyError(nombre)
                return self.incidentes

        db = BD(dict(CONFIG_DEFECTO))
        db.db = BaseFalsa()

        resultados = db.incidentes_por_categoria_semana()

        self.assertEqual(resultados[0]["semana"], "Sin fecha")
        filtro = db.db.incidentes.pipeline[0]["$match"]
        self.assertEqual(
            filtro["$expr"],
            {"$eq": [{"$type": "$fecha"}, "date"]},
        )


class TestDocumentos(unittest.TestCase):
    def test_doc_incidente(self):
        clasif = {"categoria": "sobrepeso", "prioridad": "media", "resumen": "r", "entidades": {"placa": None}}
        doc = construir_doc_incidente("a@b.c", "Asunto", "Cuerpo", clasif)
        self.assertEqual((doc["estado"], doc["clasificacion"]["categoria"], len(doc["historial"])), ("nuevo", "sobrepeso", 1))
        self.assertFalse(doc["clasificacion"]["requiere_revision_humana"])

    def test_doc_acceso_guarda_premisas_y_resultados(self):
        res = {k: True for k in "PQRSHAEDB"}
        res.update(decision="DENEGADO", semaforo="rojo", explicacion=["x"], reglas_activadas=["A"])
        doc = construir_doc_acceso("ABC-123-D", "CAM-1", res, "op1")
        for k in "PQRSHAEDB":
            self.assertIn(k, doc)
        self.assertEqual((doc["operador"], doc["decision"]), ("op1", "DENEGADO"))
        self.assertIsInstance(doc["fecha"], datetime)


if __name__ == "__main__":
    unittest.main()