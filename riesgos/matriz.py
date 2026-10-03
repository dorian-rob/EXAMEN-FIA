# -*- coding: utf-8 -*-
"""Módulo para el cálculo y evaluación de la Matriz de Riesgos Éticos 5x5."""
from config import cargar_config


class EvaluadorRiesgos:
    def __init__(self):
        self.cfg = cargar_config()
        self.umbral_critico = self.cfg.get("umbral_critico", 17)
        self.umbral_alto = self.cfg.get("umbral_alto", 10)

    def calcular_nivel(self, puntaje: int) -> str:
        """Determina el nivel de riesgo en función de los umbrales configurados."""
        if puntaje >= self.umbral_critico:
            return "Crítico"
        elif puntaje >= self.umbral_alto:
            return "Alto"
        elif puntaje >= 5:
            return "Medio"
        return "Bajo"

    def procesar_riesgo(self, riesgo: dict) -> dict:
        """Calcula el puntaje inicial, el nivel de severidad y el riesgo residual."""
        p_init = riesgo.get("probabilidad_inicial", 1)
        i_init = riesgo.get("impacto_inicial", 1)
        puntaje_inicial = p_init * i_init

        p_res = riesgo.get("probabilidad_residual", 1)
        i_res = riesgo.get("impacto_residual", 1)
        puntaje_residual = p_res * i_res

        riesgo_procesado = dict(riesgo)
        riesgo_procesado["puntaje_inicial"] = puntaje_inicial
        riesgo_procesado["nivel_inicial"] = self.calcular_nivel(puntaje_inicial)
        riesgo_procesado["puntaje_residual"] = puntaje_residual
        riesgo_procesado["nivel_residual"] = self.calcular_nivel(puntaje_residual)

        return riesgo_procesado