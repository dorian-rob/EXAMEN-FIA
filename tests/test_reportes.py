# -*- coding: utf-8 -*-
import csv
import json
import os
import tempfile
import unittest
from datetime import datetime

from db.memoria import BDMemoria
from reportes import exportar_csv, exportar_json, exportar_pdf


class TestReportes(unittest.TestCase):
    def setUp(self):
        self.db = BDMemoria()
        self.directorio = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.directorio.cleanup()

    def ruta(self, nombre):
        return os.path.join(self.directorio.name, nombre)

    def test_exportar_csv_enriquece_accesos_con_camion_y_estados(self):
        camion_id = self.db.insertar("camiones", {
            "placa": "CAM-101",
            "empresa": "Logística Express",
            "tipo_carga": "Peligrosa",
            "autorizacion": True,
            "lista_negra": False,
            "documentos_incompletos": False,
            "certificacion_valida": True,
        })
        entrada = datetime(2026, 10, 3, 9, 30)
        self.db.insertar("accesos", {
            "placa": "CAM-101",
            "camion_id": camion_id,
            "decision": "ACCESO_ESTANDAR",
            "fecha": entrada,
            "premisas": {"P": True, "Q": False, "R": True, "S": True},
            "timestamp_salida": datetime(2026, 10, 3, 11, 0),
        })
        self.db.insertar("accesos", {
            "placa": "CAM-101",
            "decision": "DENEGADO",
            "fecha": datetime(2026, 10, 4, 9, 30),
            "premisas": {"P": False, "Q": True, "R": False, "S": False},
        })

        destino = self.ruta("accesos.csv")
        self.assertEqual(exportar_csv(self.db, destino), 2)
        with open(destino, encoding="utf-8-sig", newline="") as archivo:
            filas = list(csv.DictReader(archivo))

        self.assertEqual(filas[0]["empresa_transportista"], "Logística Express")
        self.assertEqual(filas[0]["tipo_carga"], "Peligrosa")
        self.assertEqual(filas[0]["timestamp_entrada"], entrada.isoformat())
        self.assertEqual(filas[0]["timestamp_salida"], "2026-10-03T11:00:00")
        self.assertEqual(filas[0]["lista_negra"], "False")
        self.assertEqual(filas[0]["autorizacion"], "True")
        self.assertEqual(filas[0]["documentos_incompletos"], "True")
        self.assertEqual(filas[1]["timestamp_entrada"], "")
        self.assertEqual(filas[1]["decision"], "DENEGADO")

    def test_exportar_json_conserva_documentos_y_serializa_metadatos(self):
        fecha = datetime(2026, 10, 3, 12, 45)
        self.db.insertar("incidentes", {
            "fecha": fecha,
            "correo_original": "Derrame en puerta 4",
            "clasificacion": {"categoria": "Derrame", "probabilidad": 4, "impacto": 5},
        })
        self.db.insertar("evaluaciones_llm", {"modelo": "llama3.2", "puntaje_riesgo": 20})
        self.db.insertar("riesgos_eticos", {"mitigacion": "Revisión humana"})

        destino = self.ruta("analisis.json")
        self.assertEqual(exportar_json(self.db, destino), 3)
        with open(destino, encoding="utf-8") as archivo:
            reporte = json.load(archivo)

        self.assertEqual(reporte["incidentes"][0]["fecha"], fecha.isoformat())
        self.assertEqual(reporte["incidentes"][0]["correo_original"], "Derrame en puerta 4")
        self.assertEqual(reporte["evaluaciones_llm"][0]["puntaje_riesgo"], 20)
        self.assertEqual(reporte["riesgos_eticos"][0]["mitigacion"], "Revisión humana")
        self.assertEqual(reporte["configuracion_ollama"]["modelo"], "llama3.2")
        self.assertNotIn("mongo_uri", reporte["configuracion_ollama"])

    def test_exportar_json_serializa_object_id_bson(self):
        from bson import ObjectId

        self.db.insertar("evaluaciones_llm", {"categoria": "Derrame"})
        self.db.datos["evaluaciones_llm"][0]["_id"] = ObjectId()
        destino = self.ruta("object-id.json")

        exportar_json(self.db, destino)
        with open(destino, encoding="utf-8") as archivo:
            reporte = json.load(archivo)

        self.assertRegex(reporte["evaluaciones_llm"][0]["_id"], r"^[0-9a-f]{24}$")

    def test_exportar_pdf_incluye_resumen_y_solo_alertas_criticas(self):
        self.db.insertar("incidentes", {
            "fecha": datetime(2026, 10, 3, 12, 0),
            "clasificacion": {"categoria": "Derrame"},
            "resultado": {"puntaje_riesgo": 20, "categoria": "Derrame"},
            "correo_original": "Derrame de combustible en patio",
        })
        self.db.insertar("incidentes", {
            "fecha": datetime(2026, 10, 3, 13, 0),
            "clasificacion": {"categoria": "Retraso"},
            "resultado": {"puntaje_riesgo": 12, "categoria": "Retraso"},
            "correo_original": "Retraso de unidad",
        })
        self.db.insertar("incidentes", {
            "correo": "Registro anterior sin fecha",
            "resultado": {"categoria": "Otro"},
        })
        self.db.insertar("incidentes", {
            "fecha": "2026-10-03T13:30:00",
            "resultado": {"categoria": "Otro"},
        })

        destino = self.ruta("ejecutivo.pdf")
        self.assertEqual(exportar_pdf(self.db, destino), 1)
        with open(destino, "rb") as archivo:
            self.assertTrue(archivo.read().startswith(b"%PDF"))
        self.assertGreater(os.path.getsize(destino), 500)

    def test_agregacion_semanal_ignora_incidentes_sin_fecha_valida(self):
        fecha = datetime(2026, 10, 3, 12, 0)
        self.db.insertar("incidentes", {
            "fecha": fecha,
            "clasificacion": {"categoria": "Derrame"},
        })
        self.db.insertar("incidentes", {"resultado": {"categoria": "Otro"}})
        self.db.insertar("incidentes", {"fecha": None})
        self.db.insertar("incidentes", {"fecha": "2026-10-03T13:30:00"})

        self.assertEqual(
            self.db.incidentes_por_categoria_semana(),
            [{"semana": "2026-W40", "categoria": "Derrame", "total": 1}],
        )


if __name__ == "__main__":
    unittest.main()
