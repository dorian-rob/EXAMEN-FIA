# ============================================================
# PRACTICA 2 - PARTE 1
# ASISTENTE Y CHEF CREPERO DE COPITO'S CREPA HOUSE (LLM + Ollama)
# ============================================================
#
# Requisitos:
#   pip install ollama
#   ollama pull llama3.2
#   (o el modelo que tengas instalado en Ollama)
#
# Ejecutar:
#   p02primertutor_llm.py
# ============================================================

import queue
import threading
import tkinter as tk
from tkinter import scrolledtext
import ollama


# ------------------------------------------------------------
# 1. CONFIGURACIÓN DEL MODELO Y DEL NEGOCIO
# ------------------------------------------------------------

# Cambia "llama3" por "llama3.2" o el modelo exacto que tengas en 'ollama list'
MODELO = "llama3.2"

NEGOCIO = "Copito's Crepa House"

# Menú base de referencia para el negocio
MENU = {
    "Crepas dulces": {
        "Bigotes de Fresa: Nutella con fresa": 65,
        "Cajeta con nuez": 60,
        "Lechera con plátano": 55,
    },
    "Crepas saladas": {
        "Jamón y queso": 70,
        "Pollo con champiñones": 75,
    },
    "Frappes": {
        "Moka": 60,
        "Oreo": 65,
        "Fresa": 60,
        "Capuchino": 60,
    },
}


def texto_del_menu():
    """Convierte el diccionario MENU en texto para el system prompt."""
    lineas = []
    for categoria, productos in MENU.items():
        lineas.append(f"{categoria}:")
        for nombre, precio in productos.items():
            lineas.append(f"  - {nombre}: ${precio} MXN")
    return "\n".join(lineas)


# ------------------------------------------------------------
# 2. CONFIGURACIÓN DEL SISTEMA (CHEF CREPERO + ATENCIÓN)
# ------------------------------------------------------------

MENSAJE_SISTEMA = f"""
Eres Copito, el asistente virtual y Chef Crepero experto de {NEGOCIO}.
Tu mascota y logo es un gatito, así que de vez en cuando puedes decir "miau" de forma simpática.

Tu función es atender a los clientes, ofrecer el menú oficial y AYUDARLOS A CREAR O INVENTAR LA CREPA O FRAPPE PERFECTO.

MENÚ BASE DE REFERENCIA:
{texto_del_menu()}

REGLAS DE ATENCIÓN, RAZONAMIENTO Y CREATIVIDAD:
1. Saludar siempre con amabilidad y un tono cálido, alegre y juvenil.
2. Si el cliente pregunta por el menú oficial u opciones estándar, muestra los productos y precios exactos del menú base.
3. CREACIÓN DE RECETAS PERSONALIZADAS Y RAZONAMIENTO:
   - Si el cliente menciona ingredientes específicos (ej. "tengo queso crema y zarzamora", "quiero algo con plátano y oreo"), antojos o ideas, actúa como Chef Crepero.
   - Analiza los ingredientes y PROPÓN UNA RECETA O COMBINACIÓN CREATIVA de crepa o frappe.
   - Explica por qué esa combinación de ingredientes y texturas sabe rica.
   - Para calcular el precio de una crepa o frappe personalizado, toma el precio base de la categoría ($55-$65 dulces, $70 saladas, $60 frappes) y estima de forma transparente el total.
4. Si piden una combinación inusual, sugiere un ajuste amable para que quede deliciosa.
5. Si preguntan por alergias o restricciones (ej. sin lactosa, gluten), ofrece opciones o sustitutos compatibles y pide confirmación con el personal.
6. Responder siempre en español y con explicaciones claras estructuradas.
7. Si la pregunta no tiene relación con comida, crepas o bebidas, redirige amablemente hacia la crepería.
"""


# ------------------------------------------------------------
# 3. APLICACIÓN GRÁFICA
# ------------------------------------------------------------

COLOR_ROSA = "#f48fb1"
COLOR_ROSA_OSCURO = "#c2185b"
COLOR_TEXTO = "#4a1530"
COLOR_FONDO = "#fff5f8"


class CopitoApp:

    def __init__(self, root):

        self.root = root
        self.root.title(f"{NEGOCIO} - Asistente y Chef Crepero")
        self.root.geometry("780x660")
        self.root.minsize(580, 500)
        self.root.configure(bg=COLOR_FONDO)

        # Historial de la conversación (el mensaje "system" va primero)
        self.mensajes = [{"role": "system", "content": MENSAJE_SISTEMA}]

        # Cola para recibir resultados desde hilos secundarios
        self.cola = queue.Queue()

        # Evita enviar dos preguntas a la vez
        self.ocupado = False

        self._crear_interfaz()
        self._mostrar(
            "Copito",
            f"¡Miau! Bienvenido a {NEGOCIO}. Puedo mostrarte nuestro menú, o si me dices tus ingredientes "
            "favoritos, ¡puedo inventar una receta especial de crepa o frappe para ti! ¿Qué se te antoja hoy?",
            "copito",
        )

        # Revisa la cola periódicamente
        self.root.after(100, self._procesar_cola)

    # --------------------------------------------------------
    # Logo: carita de gatito dibujada con formas
    # --------------------------------------------------------

    def _dibujar_gatito(self, canvas):

        # Orejas
        canvas.create_polygon(8, 26, 12, 5, 26, 17, fill="white", outline=COLOR_TEXTO, width=2)
        canvas.create_polygon(52, 26, 48, 5, 34, 17, fill="white", outline=COLOR_TEXTO, width=2)
        # Cabeza
        canvas.create_oval(6, 14, 54, 56, fill="white", outline=COLOR_TEXTO, width=2)
        # Ojos
        canvas.create_oval(18, 29, 25, 38, fill=COLOR_TEXTO, outline="")
        canvas.create_oval(35, 29, 42, 38, fill=COLOR_TEXTO, outline="")
        # Nariz
        canvas.create_polygon(27, 41, 33, 41, 30, 45, fill=COLOR_ROSA_OSCURO, outline="")
        # Boca
        canvas.create_line(30, 45, 25, 49, fill=COLOR_TEXTO, width=2)
        canvas.create_line(30, 45, 35, 49, fill=COLOR_TEXTO, width=2)
        # Bigotes
        for y in (42, 47):
            canvas.create_line(4, y, 17, 44, fill=COLOR_TEXTO)
            canvas.create_line(56, y, 43, 44, fill=COLOR_TEXTO)

    # --------------------------------------------------------
    # Construcción de la interfaz
    # --------------------------------------------------------

    def _crear_interfaz(self):

        # Encabezado con logo
        encabezado = tk.Frame(self.root, bg=COLOR_ROSA)
        encabezado.pack(fill="x")

        logo = tk.Canvas(encabezado, width=60, height=60, bg=COLOR_ROSA, highlightthickness=0)
        logo.pack(side="left", padx=(12, 6), pady=6)
        self._dibujar_gatito(logo)

        titulos = tk.Frame(encabezado, bg=COLOR_ROSA)
        titulos.pack(side="left")

        tk.Label(
            titulos, text=NEGOCIO, font=("Segoe UI", 17, "bold"), fg=COLOR_TEXTO, bg=COLOR_ROSA
        ).pack(anchor="w")
        tk.Label(
            titulos,
            text="Crepas y Frappes - Asistente & Chef Virtual",
            font=("Segoe UI", 10),
            fg=COLOR_TEXTO,
            bg=COLOR_ROSA,
        ).pack(anchor="w")

        tk.Label(
            encabezado,
            text=f"Modelo: {MODELO}",
            font=("Segoe UI", 9),
            fg=COLOR_TEXTO,
            bg=COLOR_ROSA,
        ).pack(side="right", padx=12)

        # Área de conversación
        self.chat = scrolledtext.ScrolledText(
            self.root,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 11),
            padx=10,
            pady=10,
            bg="white",
            fg=COLOR_TEXTO,
        )
        self.chat.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        self.chat.tag_config(
            "etiqueta_cliente", foreground="#1b5eb5", font=("Segoe UI", 11, "bold")
        )
        self.chat.tag_config(
            "etiqueta_copito", foreground=COLOR_ROSA_OSCURO, font=("Segoe UI", 11, "bold")
        )
        self.chat.tag_config(
            "etiqueta_error", foreground="#c0392b", font=("Segoe UI", 11, "bold")
        )

        # Barra de estado
        self.estado = tk.StringVar(value="Listo.")
        tk.Label(
            self.root,
            textvariable=self.estado,
            anchor="w",
            font=("Segoe UI", 9),
            fg="#777777",
            bg=COLOR_FONDO,
        ).pack(fill="x", padx=12)

        # Zona de escritura
        zona = tk.Frame(self.root, bg=COLOR_FONDO)
        zona.pack(fill="x", padx=10, pady=(5, 5))

        self.entrada = tk.Entry(zona, font=("Segoe UI", 12))
        self.entrada.pack(side="left", fill="x", expand=True, ipady=6)
        self.entrada.bind("<Return>", lambda evento: self.enviar())
        self.entrada.focus()

        self.btn_enviar = tk.Button(
            zona,
            text="Enviar",
            width=10,
            command=self.enviar,
            bg=COLOR_ROSA_OSCURO,
            fg="white",
            font=("Segoe UI", 10, "bold"),
        )
        self.btn_enviar.pack(side="left", padx=(8, 0))

        # Barra de botones secundarios
        barra = tk.Frame(self.root, bg=COLOR_FONDO)
        barra.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(barra, text="Resumen del historial", command=self.mostrar_resumen).pack(
            side="left"
        )

        tk.Button(barra, text="Ver menú", command=self.mostrar_menu).pack(
            side="left", padx=8
        )

        # Botón de creatividad de la IA
        tk.Button(
            barra, text="✨ Crepa Sorpresa", command=self.sugerir_receta_creativa
        ).pack(side="left", padx=(0, 8))

        tk.Button(barra, text="Nueva conversación", command=self.reiniciar).pack(side="left")

    # --------------------------------------------------------
    # Mostrar texto en el chat
    # --------------------------------------------------------

    def _mostrar(self, autor, texto, tipo):

        self.chat.config(state="normal")
        self.chat.insert("end", f"{autor}:\n", f"etiqueta_{tipo}")
        self.chat.insert("end", f"{texto}\n\n")
        self.chat.config(state="disabled")
        self.chat.see("end")

    # --------------------------------------------------------
    # Hilos: ejecutan Ollama en segundo plano
    # --------------------------------------------------------

    def _en_segundo_plano(self, tarea, al_terminar):

        def trabajo():
            try:
                self.cola.put((al_terminar, tarea(), None))
            except Exception as error:
                self.cola.put((al_terminar, None, error))

        threading.Thread(target=trabajo, daemon=True).start()

    def _procesar_cola(self):

        try:
            while True:
                callback, resultado, error = self.cola.get_nowait()
                callback(resultado, error)
        except queue.Empty:
            pass

        self.root.after(100, self._procesar_cola)

    # --------------------------------------------------------
    # Enviar una pregunta al LLM
    # --------------------------------------------------------

    def enviar(self):

        pregunta = self.entrada.get().strip()

        if self.ocupado:
            self.estado.set("Espera a que Copito termine de responder.")
            return

        if not pregunta:
            self.estado.set("Escribe un mensaje antes de enviar.")
            return

        self.ocupado = True
        self.btn_enviar.config(state="disabled")
        self.entrada.delete(0, "end")

        self.mensajes.append({"role": "user", "content": pregunta})
        self._mostrar("Cliente", pregunta, "cliente")
        self.estado.set("🐱 Copito está pensando la respuesta...")

        copia = list(self.mensajes)

        self._en_segundo_plano(
            lambda: ollama.chat(model=MODELO, messages=copia),
            self._respuesta_lista,
        )

    def _respuesta_lista(self, respuesta, error):

        self.ocupado = False
        self.btn_enviar.config(state="normal")
        self.entrada.focus()

        if error is not None:
            self.mensajes.pop()
            self._mostrar(
                "Error",
                "No se pudo conectar con el LLM.\n"
                f"Detalle: {error}\n"
                "Verifica que Ollama esté ejecutándose y que el modelo "
                f"esté descargado (ollama pull {MODELO}).",
                "error",
            )
            self.estado.set("Error de conexión.")
            return

        contenido = respuesta["message"]["content"]
        self.mensajes.append({"role": "assistant", "content": contenido})
        self._mostrar("Copito", contenido, "copito")
        self.estado.set("Listo.")

    # --------------------------------------------------------
    # Función de Crepa / Frappe Sorpresa (IA Creativa)
    # --------------------------------------------------------

    def sugerir_receta_creativa(self):

        if self.ocupado:
            self.estado.set("Espera a que Copito termine de responder.")
            return

        prompt_creativo = (
            "¡Miau! Sorpréndeme inventando una receta original de crepa especial o frappe "
            "que combine ingredientes deliciosos. Explícame qué lleva, por qué esos sabores combinan bien "
            "y calcula el precio aproximado."
        )

        self.entrada.delete(0, "end")
        self.entrada.insert(0, prompt_creativo)
        self.enviar()

    # --------------------------------------------------------
    # Ver el menú
    # --------------------------------------------------------

    def mostrar_menu(self):

        ventana = tk.Toplevel(self.root)
        ventana.title(f"Menú - {NEGOCIO}")
        ventana.geometry("380x380")

        caja = scrolledtext.ScrolledText(
            ventana, wrap="word", font=("Segoe UI", 11), padx=10, pady=10
        )
        caja.pack(fill="both", expand=True)
        caja.insert("end", texto_del_menu())
        caja.config(state="disabled")

    # --------------------------------------------------------
    # Resumen del historial
    # --------------------------------------------------------

    def mostrar_resumen(self):

        preguntas = [m["content"] for m in self.mensajes if m["role"] == "user"]
        respuestas = [m for m in self.mensajes if m["role"] == "assistant"]

        ventana = tk.Toplevel(self.root)
        ventana.title("Resumen del historial")
        ventana.geometry("560x460")

        caja = scrolledtext.ScrolledText(
            ventana, wrap="word", font=("Segoe UI", 11), padx=10, pady=10
        )
        caja.pack(fill="both", expand=True)

        if not preguntas:
            caja.insert("end", "Aún no hay historial. ¡Escribe tu primer mensaje!")
            caja.config(state="disabled")
            return

        texto = "ESTADÍSTICAS DE LA SESIÓN\n"
        texto += f"- Mensajes del cliente: {len(preguntas)}\n"
        texto += f"- Respuestas de Copito: {len(respuestas)}\n\n"
        texto += "LO QUE PREGUNTASTE\n"

        for i, p in enumerate(preguntas, start=1):
            corta = p if len(p) <= 80 else p[:77] + "..."
            texto += f"{i}. {corta}\n"

        texto += "\nRESUMEN DE COPITO (generado por el LLM)\n🐱 Generando..."
        caja.insert("end", texto)
        caja.config(state="disabled")

        conversacion = ""
        for m in self.mensajes:
            if m["role"] == "user":
                conversacion += f"Cliente: {m['content']}\n"
            elif m["role"] == "assistant":
                conversacion += f"Copito: {m['content'][:500]}\n"

        peticion = [
            {
                "role": "system",
                "content": "Resume conversaciones en español, de forma breve y clara.",
            },
            {
                "role": "user",
                "content": "Resume en máximo 4 viñetas qué pidió o consultó el "
                "cliente y qué recetas, crepas o productos se le recomendaron:\n\n"
                + conversacion,
            },
        ]

        def al_terminar(resp, error):
            if not ventana.winfo_exists():
                return
            caja.config(state="normal")
            caja.delete("end-2l", "end")
            if error is not None:
                caja.insert("end", f"\nNo se pudo generar el resumen: {error}")
            else:
                caja.insert("end", "\n" + resp["message"]["content"])
            caja.config(state="disabled")

        self._en_segundo_plano(
            lambda: ollama.chat(model=MODELO, messages=peticion),
            al_terminar,
        )

    # --------------------------------------------------------
    # Nueva conversación
    # --------------------------------------------------------

    def reiniciar(self):

        if self.ocupado:
            self.estado.set("Espera a que Copito termine de responder.")
            return

        self.mensajes = [{"role": "system", "content": MENSAJE_SISTEMA}]
        self.chat.config(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.config(state="disabled")
        self._mostrar(
            "Copito",
            "¡Miau! Empecemos de nuevo. ¿Qué crepa, frappe o ingredientes tienes en mente?",
            "copito",
        )
        self.estado.set("Conversación reiniciada.")


# ------------------------------------------------------------
# 4. PROGRAMA PRINCIPAL
# ------------------------------------------------------------

if __name__ == "__main__":

    ventana_principal = tk.Tk()
    CopitoApp(ventana_principal)
    ventana_principal.mainloop()