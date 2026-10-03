# -*- coding: utf-8 -*-
"""Lógica proposicional del control de acceso."""
from reglas.motor import (REGLAS, SEMAFORO, VARIABLES, certificacion_vigente, evaluar_camion,
                          evaluar_reglas, horario_restringido)
from reglas.peas import PEAS_LOGISMART, texto_peas
from reglas.tablas import (analizar_reglas, tabla_verdad_completa, tabla_verdad_regla,
                           texto_tabla_regla, texto_tablas_verdad)

__all__ = ["REGLAS", "SEMAFORO", "VARIABLES", "PEAS_LOGISMART", "analizar_reglas", "certificacion_vigente",
           "evaluar_camion", "evaluar_reglas", "horario_restringido", "tabla_verdad_completa",
           "tabla_verdad_regla", "texto_peas", "texto_tabla_regla", "texto_tablas_verdad"]