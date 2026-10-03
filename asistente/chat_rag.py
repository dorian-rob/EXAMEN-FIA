# -*- coding: utf-8 -*-
"""Asistente de LogiSmart con Ollama y contexto operativo opcional de MongoDB."""
import json

import ollama
from config import cargar_config
from utils import log


class AsistenteRAG:
    def __init__(self, db_manager):
        self.db = db_manager
        self.cfg = cargar_config()
        self.modelo = self.cfg.get("modelo", "llama3.2")
        self.cliente_ollama = ollama.Client(
            host=self.cfg.get("ollama_host", "http://localhost:11434")
        )

    def responder_pregunta(self, pregunta: str) -> str:
        """Responde con Ollama y añade datos recientes de MongoDB si están disponibles."""
        registros = {}
        if hasattr(self.db, "listar"):
            for coleccion in ("camiones", "accesos", "incidentes"):
                try:
                    registros[coleccion] = self.db.listar(
                        coleccion, orden=[("fecha", -1)], limite=5
                    )
                except Exception as exc:
                    log.warning("No se pudo consultar %s para el asistente: %s", coleccion, exc)

        contexto = json.dumps(registros, ensure_ascii=False, default=str)
        instrucciones = (
            "Eres el asistente de LogiSmart. Responde siempre en español, de forma clara y útil. "
            "Puedes responder preguntas generales usando tus conocimientos; los registros de MongoDB "
            "son contexto complementario, no una condición para responder. No inventes datos internos "
            "que no aparezcan en esos registros. No rechaces preguntas cotidianas, no empieces con "
            "disculpas ni digas que necesitas contexto para preguntas generales. Da una respuesta "
            "directa, breve y sin recomendaciones contradictorias. Para una fuga o derrame de aceite "
            "en un vehículo, indica detenerse en un lugar seguro, apagar el motor cuando sea seguro, "
            "no seguir conduciendo, alejar a las personas y pedir asistencia mecánica o vial. No indiques "
            "limpiar, contener o tocar el aceite, usar herramientas, ni meterse debajo del vehículo. "
            "Si hay humo, fuego, olor fuerte a combustible o alguien estuvo expuesto, recomienda alejarse "
            "y llamar a emergencias."
        )
        consulta = (
            f"Contexto operativo disponible (puede estar vacío):\n{contexto}\n\n"
            f"Pregunta del operador:\n{pregunta}"
        )

        try:
            log.info("Enviando consulta RAG a Ollama (%s)...", self.modelo)
            respuesta = self.cliente_ollama.chat(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": instrucciones},
                    {"role": "user", "content": consulta},
                ],
            )
            return respuesta["message"]["content"]
        except Exception as exc:
            log.error("Error al consultar el asistente RAG: %s", exc)
            return f"⚠️ Error al conectar con el asistente de inteligencia artificial: {exc}"