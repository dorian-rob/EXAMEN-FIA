# -*- coding: utf-8 -*-
"""Esquemas de Pydantic para el clasificador de incidentes."""
from typing import List
from pydantic import BaseModel, Field


class ClasificacionCorreo(BaseModel):
    """Estructura estricta para la salida JSON del clasificador LLM."""
    categoria: str = Field(
        description="Categoría del incidente: Derrame, Retraso, Documentacion, Falla Mecanica, Otro"
    )
    prioridad: str = Field(
        description="Nivel de prioridad: Alta, Media, Baja"
    )
    entidades: List[str] = Field(
        default_factory=list,
        description="Lista de entidades detectadas (placas, puertas, nombres de conductores, etc.)"
    )
    resumen: str = Field(
        description="Resumen breve del incidente en una sola frase"
    )