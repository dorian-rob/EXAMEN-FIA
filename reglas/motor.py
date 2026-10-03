# -*- coding: utf-8 -*-
"""Motor de reglas (lógica proposicional) del control de acceso.

Funciones principales:
    evaluar_camion(P, Q, R, S)          reglas originales A y E
    evaluar_reglas(P, Q, R, S, H)       A, E, D, B + decisión + explicación paso a paso
"""
from datetime import date, datetime
from typing import Any, Dict, Optional

from utils import vf

# Premisas:
#   P: autorización previa | Q: peso excede el límite | R: materiales peligrosos
#   S: certificación vigente | H: horario restringido (NUEVA)
#
# Reglas originales (se conservan):
#   A = P ∧ S ∧ ¬Q        acceso estándar
#   E = P ∧ (R ∨ Q)       inspección especial
# Reglas nuevas (justificadas):
#   D = R ∧ H             materiales peligrosos NO ingresan en horario restringido
#                         (menos personal de emergencia y menor visibilidad de noche)
#   B = P ∧ ¬S            camión autorizado pero conductor sin certificación
#                         vigente: debe renovar antes de entrar (explica por qué A=F)
#
# Orden de decisión (ante la duda, seguridad):
#   1) ¬P -> DENEGADO   2) D -> DENEGADO   3) B -> DENEGADO
#   4) E -> INSPECCIÓN ESPECIAL   5) A -> ACCESO ESTÁNDAR   6) otro -> DENEGADO

VARIABLES: Dict[str, str] = {
    "P": "Vehículo con autorización previa",
    "Q": "El peso excede el límite",
    "R": "Carga con materiales peligrosos",
    "S": "Conductor con certificación vigente",
    "H": "Horario restringido para materiales peligrosos",
}

REGLAS: Dict[str, Dict[str, Any]] = {
    "A": {"nombre": "Acceso estándar", "formula": "P ∧ S ∧ ¬Q", "vars": ("P", "Q", "S"),
          "f": lambda v: v["P"] and v["S"] and not v["Q"], "tipo": "permisiva",
          "justificacion": "Original: autorizado, conductor certificado y sin exceso de peso."},
    "E": {"nombre": "Inspección especial", "formula": "P ∧ (R ∨ Q)", "vars": ("P", "Q", "R"),
          "f": lambda v: v["P"] and (v["R"] or v["Q"]), "tipo": "condicional",
          "justificacion": "Original: autorizado, pero con carga peligrosa o exceso de peso."},
    "D": {"nombre": "Diferir por horario restringido", "formula": "R ∧ H", "vars": ("R", "H"),
          "f": lambda v: v["R"] and v["H"], "tipo": "restrictiva",
          "justificacion": "Nueva: la carga peligrosa no entra en horario restringido (riesgo operativo)."},
    "B": {"nombre": "Bloqueo por certificación vencida", "formula": "P ∧ ¬S", "vars": ("P", "S"),
          "f": lambda v: v["P"] and not v["S"], "tipo": "restrictiva",
          "justificacion": "Nueva: un conductor sin certificación vigente no debe operar en el patio."},
}

SEMAFORO = {"ACCESO_ESTANDAR": "verde", "INSPECCION_ESPECIAL": "amarillo", "DENEGADO": "rojo"}


def _validar_bool(**premisas: Any) -> None:
    for nombre, valor in premisas.items():
        if not isinstance(valor, bool):
            raise TypeError(f"La premisa {nombre} debe ser bool, se recibió {type(valor).__name__}")


def evaluar_camion(P: bool, Q: bool, R: bool, S: bool) -> Dict[str, bool]:
    """Función original: A y E (se conserva por compatibilidad)."""
    _validar_bool(P=P, Q=Q, R=R, S=S)
    v = {"P": P, "Q": Q, "R": R, "S": S}
    return {"acceso_estandar": REGLAS["A"]["f"](v), "inspeccion_especial": REGLAS["E"]["f"](v)}


def evaluar_reglas(P: bool, Q: bool, R: bool, S: bool, H: bool = False) -> Dict[str, Any]:
    """Evalúa A, E, D, B, decide y devuelve la explicación paso a paso."""
    _validar_bool(P=P, Q=Q, R=R, S=S, H=H)
    v = {"P": P, "Q": Q, "R": R, "S": S, "H": H}
    r = {k: bool(d["f"](v)) for k, d in REGLAS.items()}
    A, E, D, B = r["A"], r["E"], r["D"], r["B"]

    if not P:
        decision, motivo = "DENEGADO", "no tiene autorización previa (P=F); sin P ninguna regla permisiva puede cumplirse"
    elif D:
        decision, motivo = "DENEGADO", "lleva materiales peligrosos en horario restringido (D = R ∧ H = V): se difiere el ingreso"
    elif B:
        decision, motivo = "DENEGADO", "el conductor no tiene certificación vigente (B = P ∧ ¬S = V)"
    elif E:
        causas = (["peso excedido (Q=V)"] if Q else []) + (["carga peligrosa (R=V)"] if R else [])
        decision = "INSPECCION_ESPECIAL"
        motivo = "requiere inspección especial por " + " y ".join(causas) + " (E = V)"
        if A:
            motivo += "; A también es V, así que puede ingresar después de la inspección"
    elif A:
        decision, motivo = "ACCESO_ESTANDAR", "cumple A = P ∧ S ∧ ¬Q y no activa E, D ni B"
    else:
        decision, motivo = "DENEGADO", "ninguna regla permisiva se cumple"

    explicacion = [f"{k} = {vf(v[k])}  ({VARIABLES[k]})" for k in ("P", "Q", "R", "S", "H")]
    explicacion += [
        f"¬Q = {vf(not Q)};  P ∧ S = {vf(P and S)};  A = P ∧ S ∧ ¬Q = {vf(A)}",
        f"R ∨ Q = {vf(R or Q)};  E = P ∧ (R ∨ Q) = {vf(E)}",
        f"D = R ∧ H = {vf(D)}   (regla nueva)",
        f"B = P ∧ ¬S = {vf(B)}   (regla nueva)",
        "Orden de decisión: sin P -> DENEGADO; D -> DENEGADO; B -> DENEGADO; E -> INSPECCIÓN; A -> ACCESO",
        f"RESULTADO: {decision} porque {motivo}.",
    ]
    return {**v, "A": A, "E": E, "D": D, "B": B, "decision": decision,
            "semaforo": SEMAFORO[decision], "motivo": motivo, "explicacion": explicacion,
            "reglas_activadas": [k for k, activa in r.items() if activa]}


def horario_restringido(hora: int, inicio: int, fin: int) -> bool:
    """True si la hora está dentro de la ventana restringida (admite cruce de medianoche)."""
    if inicio <= fin:
        return inicio <= hora < fin
    return hora >= inicio or hora < fin


def certificacion_vigente(vence: Optional[str], hoy: Optional[date] = None) -> bool:
    """True si la fecha 'AAAA-MM-DD' de vencimiento es hoy o posterior."""
    try:
        return datetime.strptime(str(vence), "%Y-%m-%d").date() >= (hoy or date.today())
    except ValueError:
        return False