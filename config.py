# -*- coding: utf-8 -*-
"""Configuración de LogiSmart: valores por defecto, lectura y guardado del archivo JSON.

La variable de entorno MONGO_URI, si existe, tiene prioridad sobre el archivo.
No subas logismart_config.json a Git (puede contener tu contraseña de MongoDB).
"""
import json
import os
from typing import Any, Dict

from utils import log

RUTA_CONFIG = "logismart_config.json"

CONFIG_DEFECTO: Dict[str, Any] = {
    "mongo_uri": "mongodb://localhost:27017",   # o la URI del clúster (Atlas)
    "mongo_db": "logismart_demo",               # usa TU propio nombre de BD
    "ollama_host": "http://localhost:11434",
    "modelo": "llama3.2",
    "reintentos": 2,                # reintentos del LLM si el JSON es inválido
    "timeout_llm": 120,             # segundos
    "umbral_critico": 17,           # puntaje >= 17 -> crítico (matriz 5x5)
    "umbral_alto": 10,              # puntaje >= 10 -> alto
    "horario_inicio": 22,           # horario restringido (hora de inicio)
    "horario_fin": 6,               # horario restringido (hora de fin)
    "modo_clasificacion": "hibrido",  # reglas | llm | hibrido
    "simulacion_correo": True,      # True: no envía correos reales
    "operador": "operador1",
    "correo_soporte": "soporte@logismart.example",
}


def cargar_config() -> Dict[str, Any]:
    """Lee el archivo de configuración y lo mezcla con los valores por defecto."""
    cfg = dict(CONFIG_DEFECTO)
    try:
        with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        log.warning("No se pudo leer %s (%s); se usan valores por defecto", RUTA_CONFIG, exc)
    if os.environ.get("MONGO_URI"):
        cfg["mongo_uri"] = os.environ["MONGO_URI"]
    return cfg


def guardar_config(cfg: Dict[str, Any]) -> None:
    with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)