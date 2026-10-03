# -*- coding: utf-8 -*-
"""Utilidades pequeñas que usan todos los módulos."""
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("logismart")


def ahora() -> datetime:
    """Fecha y hora actual sin microsegundos (más limpia para guardar en MongoDB)."""
    return datetime.now().replace(microsecond=0)


def vf(valor: bool) -> str:
    """True/False -> V/F (más legible en tablas de verdad)."""
    return "V" if valor else "F"