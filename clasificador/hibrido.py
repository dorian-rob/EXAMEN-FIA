# -*- coding: utf-8 -*-
"""Clasificador híbrido de incidentes por correo (LLM + Reglas de respaldo)."""
import json
import ollama
from config import cargar_config
from clasificador.esquemas import ClasificacionCorreo
from utils import log


class ClasificadorHibrido:
    def __init__(self):
        self.cfg = cargar_config()
        self.modelo = self.cfg.get("modelo", "llama3.2")
        self.reintentos = self.cfg.get("reintentos", 2)

    def clasificar_correo(self, texto_correo: str) -> dict:
        """Intenta clasificar el correo con Ollama. Si falla tras los reintentos, activa el fallback por reglas."""
        modo = self.cfg.get("modo_clasificacion", "hibrido")

        # Modo forzado solo por reglas
        if modo == "reglas":
            return self._clasificar_por_reglas(texto_correo, motivo="Modo configurado: solo reglas")

        # Intentos con el LLM
        prompt = f"""
        Eres un clasificador experto de incidentes logísticos.
        Analiza el siguiente correo y responde ÚNICAMENTE en formato JSON válido.

        Esquema esperado:
        {{
            "categoria": "Derrame" | "Retraso" | "Documentacion" | "Falla Mecanica" | "Otro",
            "prioridad": "Alta" | "Media" | "Baja",
            "entidades": ["lista de placas, puertas o nombres encontrados"],
            "resumen": "resumen en una sola frase"
        }}

        Correo a analizar:
        "{texto_correo}"
        """

        for intento in range(1, self.reintentos + 1):
            try:
                log.info("Clasificando correo con LLM (intento %d/%d)...", intento, self.reintentos)
                respuesta = ollama.chat(
                    model=self.modelo,
                    messages=[{"role": "user", "content": prompt}],
                    format="json"
                )

                contenido = respuesta["message"]["content"]
                datos_dict = json.loads(contenido)
                
                # Validación estricta con Pydantic
                validado = ClasificacionCorreo(**datos_dict)
                resultado = validado.model_dump()
                resultado["metodo"] = f"LLM ({self.modelo})"
                return resultado

            except Exception as exc:
                log.warning("Fallo en intento %d con LLM: %s", intento, exc)

        # Fallback a reglas si fallan los reintentos
        return self._clasificar_por_reglas(texto_correo, motivo="Exceso de reintentos o fallo de JSON en LLM")

    def _clasificar_por_reglas(self, texto: str, motivo: str = "") -> dict:
        """Clasificación determinista de respaldo basada en palabras clave."""
        log.info("Ejecutando clasificación por reglas de respaldo (Motivo: %s)...", motivo)
        texto_lower = texto.lower()
        
        categoria = "Otro"
        prioridad = "Baja"
        entidades = []

        if "derrame" in texto_lower or "fuga" in texto_lower or "químico" in texto_lower:
            categoria = "Derrame"
            prioridad = "Alta"
        elif "retraso" in texto_lower or "tarde" in texto_lower or "demora" in texto_lower:
            categoria = "Retraso"
            prioridad = "Media"
        elif "documento" in texto_lower or "vencid" in texto_lower or "permiso" in texto_lower:
            categoria = "Documentacion"
            prioridad = "Media"
        elif "falla" in texto_lower or "avería" in texto_lower or "motor" in texto_lower:
            categoria = "Falla Mecanica"
            prioridad = "Alta"

        # Búsqueda simple de entidades (ejemplo: palabras en mayúsculas o números de placas)
        palabras = texto.split()
        for p in palabras:
            if p.isupper() and len(p) >= 4 and any(c.isdigit() for c in p):
                entidades.append(p)

        return {
            "categoria": categoria,
            "prioridad": prioridad,
            "entidades": entidades,
            "resumen": "Clasificación automática mediante reglas de palabras clave.",
            "metodo": f"Reglas de Respaldo ({motivo})"
        }