# -*- coding: utf-8 -*-
"""Base de datos en memoria con la misma interfaz que BD.

Sirve para las pruebas unitarias y para ejecutar la interfaz sin MongoDB
(python app.py --memoria). Los datos NO se guardan al cerrar el programa.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from config import CONFIG_DEFECTO
from db.conexion import BD, COLECCIONES


def _semana_iso(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def _valor_ruta(doc: Dict[str, Any], ruta: str) -> Any:
    for parte in ruta.split("."):
        doc = doc.get(parte) if isinstance(doc, dict) else None
    return doc


def _cumple(doc: Dict[str, Any], filtro: Dict[str, Any]) -> bool:
    for campo, cond in filtro.items():
        v = _valor_ruta(doc, campo)
        if isinstance(cond, dict) and any(k.startswith("$") for k in cond):
            for op, ref in cond.items():
                if op == "$gte" and not (v is not None and v >= ref):
                    return False
                if op == "$lte" and not (v is not None and v <= ref):
                    return False
                if op == "$in" and v not in ref:
                    return False
                if op == "$ne" and v == ref:
                    return False
        elif v != cond:
            return False
    return True


class BDMemoria(BD):
    """Misma interfaz que BD pero en memoria (pruebas y modo --memoria). NO es persistente."""
    memoria = True

    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(cfg or dict(CONFIG_DEFECTO))
        self.datos: Dict[str, List[Dict[str, Any]]] = {c: [] for c in COLECCIONES}
        self._n = 0

    def conectar(self) -> bool:
        self.error = None
        return True

    @property
    def conectado(self) -> bool:
        return True

    @property
    def descripcion(self) -> str:
        return "MODO MEMORIA (no persistente)"

    def insertar(self, col, doc):
        self._n += 1
        doc = dict(doc)
        doc["_id"] = "%024x" % self._n
        self.datos[col].append(doc)
        return doc["_id"]

    def listar(self, col, filtro=None, orden=None, limite=0):
        filas = [d for d in self.datos[col] if _cumple(d, filtro or {})]
        for campo, sentido in reversed(orden or []):
            filas.sort(key=lambda d: (_valor_ruta(d, campo) is None, _valor_ruta(d, campo)),
                       reverse=(sentido == -1))
        return [dict(d) for d in (filas[:limite] if limite else filas)]

    def obtener(self, col, id_):
        return next((dict(d) for d in self.datos[col] if d["_id"] == id_), None)

    def actualizar(self, col, id_, cambios=None, agregar=None):
        for d in self.datos[col]:
            if d["_id"] == id_:
                d.update(cambios or {})
                for campo, valor in (agregar or {}).items():
                    d.setdefault(campo, []).append(valor)
                return True
        return False

    def eliminar(self, col, id_):
        antes = len(self.datos[col])
        self.datos[col] = [d for d in self.datos[col] if d["_id"] != id_]
        return len(self.datos[col]) < antes

    def contar(self, col, filtro=None):
        return sum(1 for d in self.datos[col] if _cumple(d, filtro or {}))

    def incidentes_por_categoria_semana(self, desde=None, hasta=None):
        cuenta: Dict[Tuple[str, str], int] = {}
        for d in self.datos["incidentes"]:
            f = d.get("fecha")
            if not isinstance(f, datetime):
                continue
            if (desde and f < desde) or (hasta and f > hasta):
                continue
            clasificacion = d.get("clasificacion") or {}
            categoria = clasificacion.get("categoria", "Sin categoría")
            clave = (_semana_iso(f), categoria)
            cuenta[clave] = cuenta.get(clave, 0) + 1
        return [{"semana": s, "categoria": c, "total": t}
                for (s, c), t in sorted(cuenta.items(), key=lambda kv: (kv[0][0], -kv[1]))]