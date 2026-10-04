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
        p_init = self._validar_valor(riesgo, "probabilidad_inicial")
        i_init = self._validar_valor(riesgo, "impacto_inicial")
        puntaje_inicial = p_init * i_init

        p_res = self._validar_valor(riesgo, "probabilidad_residual")
        i_res = self._validar_valor(riesgo, "impacto_residual")
        puntaje_residual = p_res * i_res

        riesgo_procesado = dict(riesgo)
        riesgo_procesado["puntaje_inicial"] = puntaje_inicial
        riesgo_procesado["nivel_inicial"] = self.calcular_nivel(puntaje_inicial)
        riesgo_procesado["puntaje_residual"] = puntaje_residual
        riesgo_procesado["nivel_residual"] = self.calcular_nivel(puntaje_residual)

        return riesgo_procesado

    @staticmethod
    def _validar_valor(riesgo: dict, campo: str) -> int:
        valor = riesgo.get(campo)
        if isinstance(valor, bool) or not isinstance(valor, int) or not 1 <= valor <= 5:
            raise ValueError(f"{campo} debe ser un número entero entre 1 y 5.")
        return valor