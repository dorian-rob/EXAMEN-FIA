# -*- coding: utf-8 -*-
"""Exportación de bitácoras de accesos y datos de la flota a CSV."""
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


COLUMNAS = (
    "placa",
    "empresa_transportista",
    "tipo_carga",
    "documentos_incompletos",
    "certificacion_valida",
    "timestamp_entrada",
    "timestamp_salida",
    "timestamp_evaluacion",
    "autorizacion",
    "lista_negra",
    "decision",
)


def _texto(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, (dict, list, tuple)):
        return json.dumps(valor, ensure_ascii=False, default=str)
    return str(valor)


def _buscar_camion(acceso: dict, por_id: dict, por_placa: dict) -> dict:
    camion_id = acceso.get("camion_id")
    camion = por_id.get(str(camion_id)) if camion_id is not None else None
    if camion is None and acceso.get("placa") is not None:
        camion = por_placa.get(str(acceso["placa"]).upper())
    return camion or {}


def exportar_csv(db: Any, destino: str | Path) -> int:
    """Guarda un CSV de accesos enriquecido con la ficha de cada camión.

    Devuelve el número de eventos de acceso exportados. La entrada se deriva
    de la fecha del evento solo cuando no consta una denegación; la salida
    queda vacía si no fue registrada explícitamente.
    """
    accesos = db.listar("accesos", orden=[("fecha", 1)])
    camiones = db.listar("camiones")
    por_id = {
        str(camion["_id"]): camion
        for camion in camiones
        if camion.get("_id") is not None
    }
    por_placa = {
        str(camion["placa"]).upper(): camion
        for camion in camiones
        if camion.get("placa") is not None
    }

    with Path(destino).open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        for acceso in accesos:
            camion = _buscar_camion(acceso, por_id, por_placa)
            premisas = acceso.get("premisas") or {}
            fecha_evento = acceso.get("timestamp") or acceso.get("fecha")
            denegado = str(acceso.get("decision", "")).upper() in {
                "DENEGADO", "DENEGADA", "RECHAZADO", "RECHAZADA"
            }
            entrada = acceso.get("timestamp_entrada")
            if entrada is None and not denegado:
                entrada = fecha_evento
            fila = {
                "placa": acceso.get("placa") or camion.get("placa"),
                "empresa_transportista": acceso.get(
                    "empresa", camion.get("empresa")
                ),
                "tipo_carga": acceso.get("tipo_carga", camion.get("tipo_carga")),
                "documentos_incompletos": acceso.get(
                    "documentos_incompletos",
                    premisas.get("R", camion.get("documentos_incompletos")),
                ),
                "certificacion_valida": acceso.get(
                    "certificacion_valida",
                    premisas.get("S", camion.get("certificacion_valida")),
                ),
                "timestamp_entrada": entrada,
                "timestamp_salida": acceso.get("timestamp_salida"),
                "timestamp_evaluacion": fecha_evento,
                "autorizacion": acceso.get(
                    "autorizacion", premisas.get("P", camion.get("autorizacion"))
                ),
                "lista_negra": acceso.get(
                    "lista_negra", premisas.get("Q", camion.get("lista_negra"))
                ),
                "decision": acceso.get("decision"),
            }
            escritor.writerow({clave: _texto(valor) for clave, valor in fila.items()})
    return len(accesos)
