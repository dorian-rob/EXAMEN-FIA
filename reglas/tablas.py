# -*- coding: utf-8 -*-
"""Tablas de verdad y análisis de las reglas (redundancias, excluyentes, conflictos)."""
import itertools
from typing import Any, Dict, List

from reglas.motor import REGLAS, evaluar_reglas
from utils import vf


def tabla_verdad_regla(clave: str) -> List[Dict[str, bool]]:
    """Tabla de verdad de una regla sobre sus propias variables."""
    regla = REGLAS[clave]
    filas = []
    for valores in itertools.product([True, False], repeat=len(regla["vars"])):
        v = dict(zip(regla["vars"], valores))
        filas.append({**v, clave: bool(regla["f"](v))})
    return filas


def tabla_verdad_completa() -> List[Dict[str, Any]]:
    """32 combinaciones de (P,Q,R,S,H) con A, E, D, B y la decisión final."""
    filas = []
    for P, Q, R, S, H in itertools.product([True, False], repeat=5):
        res = evaluar_reglas(P, Q, R, S, H)
        filas.append({"P": P, "Q": Q, "R": R, "S": S, "H": H, "A": res["A"], "E": res["E"],
                      "D": res["D"], "B": res["B"], "decision": res["decision"]})
    return filas


def texto_tabla_regla(clave: str) -> str:
    regla = REGLAS[clave]
    cols = list(regla["vars"]) + [clave]
    L = [f"{clave} = {regla['formula']}   [{regla['nombre']}]", "  " + regla["justificacion"],
         "  " + " ".join(f"{c:^3}" for c in cols), "  " + "-" * (4 * len(cols))]
    for fila in tabla_verdad_regla(clave):
        L.append("  " + " ".join(f"{vf(fila[c]):^3}" for c in cols))
    return "\n".join(L)


def texto_tablas_verdad() -> str:
    partes = [texto_tabla_regla(k) for k in REGLAS]
    L = ["TABLA COMPLETA (32 combinaciones)", "  P  Q  R  S  H | A  E  D  B | Decisión", "  " + "-" * 46]
    for f in tabla_verdad_completa():
        L.append("  " + "  ".join(vf(f[c]) for c in "PQRSH") + " | " +
                 "  ".join(vf(f[c]) for c in "AEDB") + " | " + f["decision"])
    return "\n\n".join(partes) + "\n\n" + "\n".join(L)


def analizar_reglas() -> List[str]:
    """RETO OPCIONAL: detecta reglas redundantes, excluyentes y conflictos."""
    vectores: Dict[str, List[bool]] = {k: [] for k in REGLAS}
    for P, Q, R, S, H in itertools.product([True, False], repeat=5):
        v = {"P": P, "Q": Q, "R": R, "S": S, "H": H}
        for k, d in REGLAS.items():
            vectores[k].append(bool(d["f"](v)))
    informe = []
    for a, b in itertools.combinations(REGLAS, 2):
        va, vb = vectores[a], vectores[b]
        ambas = sum(x and y for x, y in zip(va, vb))
        if va == vb:
            informe.append(f"REDUNDANTES: {a} y {b} dan el mismo resultado en las 32 combinaciones.")
        elif ambas == 0:
            informe.append(f"EXCLUYENTES: {a} y {b} nunca son V a la vez (no hay contradicción posible).")
        else:
            nota = ""
            if all(y for x, y in zip(va, vb) if x):
                nota = f" {a} implica {b}."
            elif all(x for x, y in zip(va, vb) if y):
                nota = f" {b} implica {a}."
            tipos = {REGLAS[a]["tipo"], REGLAS[b]["tipo"]}
            if "permisiva" in tipos and ("restrictiva" in tipos or "condicional" in tipos):
                nota += " Conflicto permisiva/restrictiva: lo resuelve el orden de decisión (gana la más segura)."
            informe.append(f"CONCURRENTES: {a} y {b} coinciden en {ambas}/32 combinaciones.{nota}")
    sin_regla = sum(1 for f in tabla_verdad_completa()
                    if f["decision"] == "DENEGADO" and f["P"] and not f["D"] and not f["B"]
                    and not f["E"] and not f["A"])
    informe.append("COBERTURA: " + ("todas las combinaciones con P=V caen en alguna regla."
                                    if sin_regla == 0 else f"{sin_regla} combinaciones sin regla aplicable."))
    return informe