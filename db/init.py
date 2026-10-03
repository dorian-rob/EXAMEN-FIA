# -*- coding: utf-8 -*-
"""Capa de persistencia."""
from db.conexion import BD, COLECCIONES, ErrorBD
from db.documentos import construir_doc_acceso, construir_doc_incidente
from db.memoria import BDMemoria

__all__ = ["BD", "BDMemoria", "COLECCIONES", "ErrorBD", "construir_doc_acceso", "construir_doc_incidente"]