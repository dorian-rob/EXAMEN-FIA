# -*- coding: utf-8 -*-
"""Exportación de datos técnicos de incidentes, evaluaciones y riesgos a JSON."""
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


COLECCIONES_REPORTE = ("incidentes", "evaluaciones_llm", "riesgos_eticos")
CLAVES_CONFIG_OLLAMA = (
    "ollama_host",
    "modelo",
    "modo_clasificacion",
    "reintentos",
    "timeout_llm",
)


def _serializar(valor: Any) -> str:
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if valor.__class__.__name__ == "ObjectId":
        return str(valor)
    raise TypeError(f"Tipo no serializable en el reporte JSON: {type(valor).__name__}")


def exportar_json(db: Any, destino: str | Path) -> int:
    """Exporta los documentos completos de análisis y riesgos.

    El resultado conserva los campos originales y serializa fechas como ISO
    8601 e identificadores BSON como cadenas. Devuelve el total de documentos.
    """
    documentos = {nombre: db.listar(nombre) for nombre in COLECCIONES_REPORTE}
    configuracion = getattr(db, "cfg", {})
    reporte = {
        "generado_en": datetime.now().replace(microsecond=0).isoformat(),
        "configuracion_ollama": {
            clave: configuracion[clave]
            for clave in CLAVES_CONFIG_OLLAMA
            if clave in configuracion
        },
        **documentos,
    }
    with Path(destino).open("w", encoding="utf-8") as archivo:
        json.dump(reporte, archivo, ensure_ascii=False, indent=2, default=_serializar)
        archivo.write("\n")
    return sum(len(filas) for filas in documentos.values())
