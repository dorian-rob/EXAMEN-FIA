# -*- coding: utf-8 -*-
"""Script para poblar la base de datos MongoDB con datos iniciales de demostración."""
from config import cargar_config
from db.conexion import BD
from utils import log, ahora


def cargar_datos_demostracion():
    cfg = cargar_config()
    db = BD(cfg)
    db.conectar()

    log.info("Iniciando carga de datos de demostración...")

    camiones_demo = [
        {
            "placa": "CAM-101",
            "empresa": "Logística Express",
            "autorizacion": True,
            "lista_negra": False,
            "documentos_incompletos": False,
            "certificacion_valida": True,
            "tipo_carga": "General"
        },
        {
            "placa": "CAM-102",
            "empresa": "TransNorte",
            "autorizacion": True,
            "lista_negra": False,
            "documentos_incompletos": True,
            "certificacion_valida": True,
            "tipo_carga": "Peligrosa"
        }
    ]
    riesgos_demo = [
        {
            "modulo": "IA Clasificadora",
            "descripcion": "Extracción errónea de entidades",
            "probabilidad_inicial": 4,
            "impacto_inicial": 4,
            "mitigacion": "Validación Pydantic y reglas de respaldo",
            "probabilidad_residual": 2,
            "impacto_residual": 2,
        },
        {
            "modulo": "Control de acceso",
            "descripcion": "Decisión incorrecta ante fallo de datos",
            "probabilidad_inicial": 3,
            "impacto_inicial": 5,
            "mitigacion": "Evaluación determinista y revisión operativa",
            "probabilidad_residual": 1,
            "impacto_residual": 3,
        },
    ]

    try:
        if db.conectado:
            for c in camiones_demo:
                db.insertar("camiones", c)
            if db.contar("riesgos_eticos") == 0:
                for riesgo in riesgos_demo:
                    db.insertar("riesgos_eticos", {**riesgo, "creado_en": ahora()})
            log.info("✅ Base de datos poblada exitosamente!")
        else:
            log.error("No se pudo conectar a MongoDB: %s", db.error)

    except Exception as exc:
        log.error("Error al poblar la base de datos: %s", exc)
    finally:
        db.cerrar()


if __name__ == "__main__":
    cargar_datos_demostracion()