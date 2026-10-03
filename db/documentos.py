# -*- coding: utf-8 -*-
"""Constructores de los documentos que se guardan en MongoDB (accesos e incidentes)."""
from datetime import datetime
from typing import Any, Dict, Optional

from utils import ahora


def construir_doc_acceso(placa: str, camion_id: str, res: Dict[str, Any], operador: str,
                         fecha: Optional[datetime] = None) -> Dict[str, Any]:
    """Documento de la bitácora: premisas, resultados A/E (y D/B), marca de tiempo, operador."""
    return {"fecha": fecha or ahora(), "operador": operador, "placa": placa, "camion_id": camion_id,
            **{k: res[k] for k in ("P", "Q", "R", "S", "H", "A", "E", "D", "B")},
            "decision": res["decision"], "semaforo": res["semaforo"],
            "explicacion": res["explicacion"], "reglas_activadas": res["reglas_activadas"]}


def construir_doc_incidente(remitente: str, asunto: str, cuerpo: str, clasif: Dict[str, Any],
                            correo: Optional[Dict[str, Any]] = None, estado: str = "nuevo",
                            fecha: Optional[datetime] = None, evento: str = "Incidente creado") -> Dict[str, Any]:
    fecha = fecha or ahora()
    return {"fecha": fecha, "remitente": remitente, "asunto": asunto, "correo_original": cuerpo,
            "clasificacion": {"categoria": clasif["categoria"], "prioridad": clasif["prioridad"],
                              "resumen": clasif.get("resumen", ""),
                              "requiere_revision_humana": bool(clasif.get("requiere_revision_humana", False)),
                              "origen": clasif.get("origen", "manual")},
            "datos_extraidos": clasif.get("entidades", {}), "estado": estado,
            "correo_soporte": correo or {}, "historial": [{"fecha": fecha, "evento": evento}]}