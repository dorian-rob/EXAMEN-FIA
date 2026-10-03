# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest

import config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.viejo = config.RUTA_CONFIG
        self.dir = tempfile.TemporaryDirectory()
        config.RUTA_CONFIG = os.path.join(self.dir.name, "cfg.json")
        os.environ.pop("MONGO_URI", None)

    def tearDown(self):
        config.RUTA_CONFIG = self.viejo
        os.environ.pop("MONGO_URI", None)
        self.dir.cleanup()

    def test_sin_archivo_usa_valores_por_defecto(self):
        self.assertEqual(config.cargar_config(), config.CONFIG_DEFECTO)

    def test_guardar_y_cargar(self):
        cfg = config.cargar_config()
        cfg["modelo"] = "mistral"
        config.guardar_config(cfg)
        self.assertEqual(config.cargar_config()["modelo"], "mistral")

    def test_archivo_corrupto_no_rompe(self):
        with open(config.RUTA_CONFIG, "w") as f:
            f.write("{no es json")
        self.assertEqual(config.cargar_config(), config.CONFIG_DEFECTO)

    def test_variable_de_entorno_tiene_prioridad(self):
        config.guardar_config({**config.CONFIG_DEFECTO, "mongo_uri": "mongodb://archivo"})
        os.environ["MONGO_URI"] = "mongodb://entorno"
        self.assertEqual(config.cargar_config()["mongo_uri"], "mongodb://entorno")


if __name__ == "__main__":
    unittest.main()