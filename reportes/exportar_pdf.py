# -*- coding: utf-8 -*-
"""Generación del informe ejecutivo semanal de incidentes en PDF."""
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _puntaje_riesgo(documento: dict) -> int | float | None:
    """Busca la puntuación inicial en las formas habituales de los documentos."""
    nombres = {"puntaje_riesgo", "puntaje_inicial", "puntaje", "risk_score"}
    pendientes = [documento]
    while pendientes:
        actual = pendientes.pop()
        if isinstance(actual, dict):
            for clave, valor in actual.items():
                if clave.lower() in nombres and isinstance(valor, (int, float)):
                    return valor
                if isinstance(valor, (dict, list)):
                    pendientes.append(valor)
        elif isinstance(actual, list):
            pendientes.extend(actual)
    return None


def _texto(documento: dict, *claves: str) -> str:
    for clave in claves:
        valor = documento.get(clave)
        if valor not in (None, ""):
            return str(valor)
    return "Sin descripción"


def exportar_pdf(db: Any, destino: str | Path) -> int:
    """Genera el informe semanal y una tabla de incidentes con puntaje >= 17.

    Devuelve el número de incidentes críticos incluidos en el informe.
    """
    resumen = db.incidentes_por_categoria_semana()
    incidentes = db.listar("incidentes")
    criticos = [
        (incidente, puntaje)
        for incidente in incidentes
        if (puntaje := _puntaje_riesgo(incidente)) is not None and puntaje >= 17
    ]

    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloLogiSmart",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#24364b"),
        spaceAfter=4 * mm,
    )
    celda = ParagraphStyle("CeldaLogiSmart", parent=estilos["BodyText"], fontSize=8, leading=10)
    subtitulo = ParagraphStyle(
        "SubtituloLogiSmart", parent=estilos["Heading2"], textColor=colors.HexColor("#24364b")
    )
    documento_pdf = SimpleDocTemplate(
        str(destino),
        pagesize=landscape(letter),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Informe ejecutivo de LogiSmart",
        author="LogiSmart",
    )

    contenido = [
        Paragraph("LogiSmart", titulo),
        Paragraph(
            f"Informe ejecutivo de incidentes · Emitido: "
            f"{datetime.now().astimezone().isoformat(timespec='seconds')}",
            estilos["Normal"],
        ),
        Spacer(1, 6 * mm),
        Paragraph("Incidentes por categoría y semana ISO", subtitulo),
    ]

    filas_resumen = [["Semana ISO", "Categoría", "Total"]]
    filas_resumen.extend(
        [
            [
                Paragraph(escape(str(fila.get("semana", ""))), celda),
                Paragraph(escape(str(fila.get("categoria") or "Sin categoría")), celda),
                str(fila.get("total", 0)),
            ]
            for fila in resumen
        ]
    )
    if len(filas_resumen) == 1:
        filas_resumen.append(["Sin incidentes registrados", "", ""])
    tabla_resumen = Table(filas_resumen, colWidths=[50 * mm, 100 * mm, 25 * mm], repeatRows=1)
    tabla_resumen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24364b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1dc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f4f8")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    contenido.extend([tabla_resumen, Spacer(1, 7 * mm)])
    contenido.append(Paragraph(f"Alertas críticas (puntaje de riesgo ≥ 17): {len(criticos)}", subtitulo))

    filas_criticos = [["Fecha", "Categoría", "Puntaje", "Descripción reportada"]]
    for incidente, puntaje in criticos:
        fecha = incidente.get("fecha") or incidente.get("timestamp")
        narrativa = _texto(
            incidente,
            "correo_original",
            "correo",
            "descripcion",
            "narrativa",
            "asunto",
        )
        clasificacion = incidente.get("clasificacion") or incidente.get("resultado") or {}
        categoria = (
            clasificacion.get("categoria", "Sin categoría")
            if isinstance(clasificacion, dict)
            else str(clasificacion)
        )
        filas_criticos.append(
            [
                Paragraph(escape(str(fecha or "Sin fecha")), celda),
                Paragraph(escape(str(categoria)), celda),
                str(puntaje),
                Paragraph(escape(narrativa), celda),
            ]
        )
    if len(filas_criticos) == 1:
        filas_criticos.append(["Sin incidentes críticos", "", "", ""])
    tabla_criticos = Table(
        filas_criticos,
        colWidths=[38 * mm, 40 * mm, 20 * mm, 145 * mm],
        repeatRows=1,
    )
    tabla_criticos.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#9b2c2c")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1dc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff3f1")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    contenido.append(tabla_criticos)
    documento_pdf.build(contenido)
    return len(criticos)
