# -*- coding: utf-8 -*-
"""Conexión a MongoDB y operaciones genéricas (CRUD + una agregación).

Todas las operaciones lanzan ErrorBD con un mensaje claro si no hay conexión
o si MongoDB falla, para que la interfaz pueda mostrarlo sin romperse.
"""
import functools
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    from bson import ObjectId
except ImportError:  # pragma: no cover
    MongoClient, PyMongoError, ObjectId = None, Exception, None

# Colecciones del sistema
COLECCIONES = (
    "camiones",
    "accesos",
    "incidentes",
    "riesgos_eticos",
    "evaluaciones_llm"
)


class ErrorBD(Exception):
    """Error de base de datos con mensaje apto para mostrar al usuario."""


def _seguro(func):
    """Decorador: valida la conexión y traduce errores de pymongo a ErrorBD."""
    @functools.wraps(func)
    def envoltura(self, *args, **kwargs):
        if not self.conectado:
            raise ErrorBD(
                "No hay conexión con MongoDB. Revisa la pestaña Configuración "
                "(URI, red o IP permitida en Atlas) y pulsa 'Guardar y reconectar'."
            )
        try:
            return func(self, *args, **kwargs)
        except PyMongoError as exc:
            raise ErrorBD(f"La operación en MongoDB falló: {exc}") from exc
    return envoltura


class BD:
    """Acceso a MongoDB con CRUD genérico y una agregación."""
    memoria = False

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg
        self.cliente = None
        self.db = None
        self.error = None

    def conectar(self) -> bool:
        self.cerrar()
        if MongoClient is None:
            self.error = (
                "La biblioteca 'pymongo' no está instalada "
                "(pip install pymongo)."
            )
            return False
        try:
            self.cliente = MongoClient(
                self.cfg["mongo_uri"],
                serverSelectionTimeoutMS=3000
            )
            self.cliente.admin.command("ping")
            self.db = self.cliente[self.cfg["mongo_db"]]
            self.error = None
            return True
        except Exception as exc:
            self.db = None
            self.error = f"No se pudo conectar a MongoDB: {exc}"
            return False

    def cerrar(self) -> None:
        if self.cliente is not None:
            try:
                self.cliente.close()
            except Exception:
                pass
        self.cliente, self.db = None, None

    @property
    def conectado(self) -> bool:
        return self.db is not None

    @property
    def descripcion(self) -> str:
        return f"MongoDB · base '{self.cfg['mongo_db']}'"

    @staticmethod
    def _oid(valor: Any) -> Any:
        try:
            return ObjectId(valor) if ObjectId is not None else valor
        except Exception:
            return valor

    @_seguro
    def insertar(self, col: str, doc: Dict[str, Any]) -> str:
        return str(self.db[col].insert_one(doc).inserted_id)

    @_seguro
    def listar(
        self,
        col: str,
        filtro: Optional[Dict[str, Any]] = None,
        orden: Optional[List[Tuple[str, int]]] = None,
        limite: int = 0
    ) -> List[Dict[str, Any]]:
        cursor = self.db[col].find(filtro or {})
        if orden:
            cursor = cursor.sort(orden)
        if limite:
            cursor = cursor.limit(limite)
        return list(cursor)

    @_seguro
    def obtener(self, col: str, id_: str) -> Optional[Dict[str, Any]]:
        return self.db[col].find_one({"_id": self._oid(id_)})

    @_seguro
    def actualizar(
        self,
        col: str,
        id_: str,
        cambios: Optional[Dict[str, Any]] = None,
        agregar: Optional[Dict[str, Any]] = None
    ) -> bool:
        op: Dict[str, Any] = {}
        if cambios:
            op["$set"] = cambios
        if agregar:
            op["$push"] = agregar
        return self.db[col].update_one(
            {"_id": self._oid(id_)}, op
        ).matched_count > 0

    @_seguro
    def eliminar(self, col: str, id_: str) -> bool:
        return self.db[col].delete_one(
            {"_id": self._oid(id_)}
        ).deleted_count > 0

    @_seguro
    def contar(self, col: str, filtro: Optional[Dict[str, Any]] = None) -> int:
        return self.db[col].count_documents(filtro or {})

    @_seguro
    def incidentes_por_categoria_semana(
        self,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """AGREGACIÓN: incidentes por categoría y semana ISO."""
        pipeline: List[Dict[str, Any]] = []
        rango = {
            k: v for k, v in (("$gte", desde), ("$lte", hasta)) if v is not None
        }
        if rango:
            pipeline.append({"$match": {"fecha": rango}})

        pipeline += [
            {
                "$group": {
                    "_id": {
                        "categoria": "$clasificacion.categoria",
                        "anio": {"$isoWeekYear": "$fecha"},
                        "semana": {"$isoWeek": "$fecha"}
                    },
                    "total": {"$sum": 1}
                }
            },
            {"$sort": {"_id.anio": 1, "_id.semana": 1, "total": -1}},
        ]

        resultados = []
        for r in self.db["incidentes"].aggregate(pipeline):
            semana_fmt = f"{r['_id']['anio']}-W{r['_id']['semana']:02d}"
            resultados.append({
                "semana": semana_fmt,
                "categoria": r["_id"]["categoria"],
                "total": r["total"]
            })
        return resultados