# -*- coding: utf-8 -*-
"""Interfaz de escritorio LogiSmart con tema nocturno de Halloween."""
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

from asistente.chat_rag import AsistenteRAG
from clasificador.hibrido import ClasificadorHibrido
from config import cargar_config, guardar_config
from db.conexion import BD
from db.memoria import BDMemoria
from reportes import exportar_csv, exportar_json, exportar_pdf
from reglas.motor import evaluar_reglas
from riesgos.matriz import EvaluadorRiesgos
from utils import ahora, log


COLORES = {
    "fondo": "#05030A", "noche": "#0F0A1C", "panel": "#1A102F",
    "borde": "#3B1C63", "naranja": "#FF7A00", "verde": "#10B981",
    "neon": "#9D4EDD", "texto": "#F4EFFA", "suave": "#A99DB8",
    "entrada": "#100B1D", "rojo": "#FB5364", "amarillo": "#F5C451",
}


class VentanaPrincipal:
    VISTAS = {
        "acceso": ("Control de Acceso", "Evaluación operativa de vehículos y permisos"),
        "clasificador": ("Clasificador de Correos", "Incidentes etiquetados con IA y reglas de respaldo"),
        "asistente": ("Asistente Chat", "Consulta a Ollama con contexto de LogiSmart"),
        "riesgos": ("Matriz de Riesgos", "Seguimiento de exposición y mitigaciones"),
        "reportes": ("Reportes", "Exporta bitácoras, análisis y alertas ejecutivas"),
        "configuracion": ("Configuración", "Conexiones y preferencias del sistema"),
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LogiSmart | Centro de operaciones")
        self.root.geometry("1320x860")
        self.root.minsize(1080, 720)
        self.root.configure(bg=COLORES["fondo"])
        self.cfg = cargar_config()
        self.modo_memoria = getattr(root, "usar_memoria", False)
        self.db = self._crear_db()
        if not self.db.conectar():
            log.error("No se pudo conectar a MongoDB al iniciar: %s", self.db.error)
        self.clasificador = ClasificadorHibrido()
        self.asistente = AsistenteRAG(self.db)
        self.evaluador_riesgos = EvaluadorRiesgos()
        self.botones_nav = {}
        self.vistas = {}
        self._configurar_estilos()
        self._construir_interfaz()
        self._mostrar_vista("acceso")
        self._actualizar_kpis()

    def _crear_db(self):
        return BDMemoria(self.cfg) if self.modo_memoria else BD(self.cfg)

    def _configurar_estilos(self):
        estilo = ttk.Style(self.root)
        estilo.theme_use("clam")
        estilo.configure("Logi.Treeview", background=COLORES["entrada"], foreground=COLORES["texto"],
                         fieldbackground=COLORES["entrada"], rowheight=34, borderwidth=0,
                         font=("Segoe UI", 10))
        estilo.configure("Logi.Treeview.Heading", background=COLORES["panel"], foreground=COLORES["suave"],
                         relief="flat", font=("Segoe UI", 9, "bold"), padding=(10, 9))
        estilo.map("Logi.Treeview", background=[("selected", COLORES["borde"])],
                   foreground=[("selected", COLORES["texto"])])

    def _construir_interfaz(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self._crear_header()
        self._crear_sidebar()
        self.contenido = tk.Frame(self.root, bg=COLORES["noche"])
        self.contenido.grid(row=1, column=1, sticky="nsew")
        self.contenido.grid_columnconfigure(0, weight=1)
        self.contenido.grid_rowconfigure(3, weight=1)
        self.lbl_titulo_vista = tk.Label(self.contenido, text="", bg=COLORES["noche"], fg=COLORES["texto"],
                                         font=("Segoe UI Semibold", 21), anchor="w")
        self.lbl_titulo_vista.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 2))
        self.lbl_subtitulo_vista = tk.Label(self.contenido, text="", bg=COLORES["noche"], fg=COLORES["suave"],
                                            font=("Segoe UI", 10), anchor="w")
        self.lbl_subtitulo_vista.grid(row=1, column=0, sticky="ew", padx=29, pady=(0, 18))
        self._crear_kpis()
        self.area_vistas = tk.Frame(self.contenido, bg=COLORES["noche"])
        self.area_vistas.grid(row=3, column=0, sticky="nsew", padx=28, pady=(20, 24))
        self.area_vistas.grid_columnconfigure(0, weight=1)
        self.area_vistas.grid_rowconfigure(0, weight=1)
        builders = {
            "acceso": self._crear_vista_acceso,
            "clasificador": self._crear_vista_clasificador,
            "asistente": self._crear_vista_asistente,
            "riesgos": self._crear_vista_riesgos,
            "reportes": self._crear_vista_reportes,
            "configuracion": self._crear_vista_configuracion,
        }
        for clave, crear in builders.items():
            vista = tk.Frame(self.area_vistas, bg=COLORES["noche"])
            vista.grid(row=0, column=0, sticky="nsew")
            vista.grid_columnconfigure(0, weight=1)
            vista.grid_rowconfigure(0, weight=1)
            self.vistas[clave] = vista
            crear(vista)

    def _crear_header(self):
        header = tk.Frame(self.root, bg=COLORES["fondo"], height=76,
                          highlightbackground=COLORES["borde"], highlightthickness=1)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text="🎃", bg=COLORES["fondo"], fg=COLORES["naranja"],
                 font=("Segoe UI Emoji", 23)).grid(row=0, column=0, padx=(24, 11), pady=13)
        titulo = tk.Frame(header, bg=COLORES["fondo"])
        titulo.grid(row=0, column=1, sticky="w", pady=12)
        tk.Label(titulo, text="LogiSmart", bg=COLORES["fondo"], fg=COLORES["texto"],
                 font=("Segoe UI Semibold", 19)).pack(anchor="w")
        tk.Label(titulo, text="CENTRO DE OPERACIONES  /  TURNO NOCTURNO",
                 bg=COLORES["fondo"], fg=COLORES["suave"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        estado_color = COLORES["verde"] if self.db.conectado else COLORES["rojo"]
        estado_texto = "MongoDB conectado" if self.db.conectado else "MongoDB desconectado"
        if self.modo_memoria:
            estado_color, estado_texto = COLORES["amarillo"], "Modo memoria"
        self.lbl_estado_db = tk.Label(header, text=f"●  {estado_texto}", bg=COLORES["panel"],
                                      fg=estado_color, font=("Segoe UI", 9, "bold"), padx=13, pady=8)
        self.lbl_estado_db.grid(row=0, column=2, padx=(8, 10), pady=14)
        self.lbl_modelo = tk.Label(header, text=f"✦  {self.cfg.get('modelo', 'llama3.2')}",
                                   bg=COLORES["panel"], fg=COLORES["neon"],
                                   font=("Segoe UI", 9, "bold"), padx=13, pady=8)
        self.lbl_modelo.grid(row=0, column=3, padx=(0, 24), pady=14)

    def _crear_sidebar(self):
        sidebar = tk.Frame(self.root, bg=COLORES["fondo"], width=236)
        sidebar.grid(row=1, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(8, weight=1)
        tk.Label(sidebar, text="ESPACIO DE TRABAJO", bg=COLORES["fondo"], fg=COLORES["suave"],
                 font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w", padx=22, pady=(24, 13))
        items = [("acceso", "⌂", "Control de Acceso"), ("clasificador", "✉", "Clasificador de Correos"),
                 ("asistente", "☾", "Asistente Chat (RAG)"), ("riesgos", "⚗", "Matriz de Riesgos"),
                 ("reportes", "▤", "Reportes")]
        for fila, (clave, icono, texto) in enumerate(items, start=1):
            boton = tk.Button(sidebar, text=f"  {icono}     {texto}", anchor="w", relief="flat", bd=0,
                              bg=COLORES["fondo"], fg=COLORES["suave"], activebackground=COLORES["panel"],
                              activeforeground=COLORES["texto"], font=("Segoe UI", 10), padx=13, pady=12,
                              cursor="hand2", command=lambda k=clave: self._mostrar_vista(k))
            boton.grid(row=fila, column=0, sticky="ew", padx=12, pady=3)
            self.botones_nav[clave] = boton
        tk.Frame(sidebar, bg=COLORES["borde"], height=1).grid(row=6, column=0, sticky="ew", padx=20, pady=15)
        boton_config = tk.Button(sidebar, text="  ⚙     Configuración", anchor="w", relief="flat", bd=0,
                                 bg=COLORES["fondo"], fg=COLORES["suave"], activebackground=COLORES["panel"],
                                 activeforeground=COLORES["texto"], font=("Segoe UI", 10), padx=13, pady=12,
                                 cursor="hand2", command=lambda: self._mostrar_vista("configuracion"))
        boton_config.grid(row=7, column=0, sticky="ew", padx=12, pady=3)
        self.botones_nav["configuracion"] = boton_config
        tk.Label(sidebar, text="✦  El sistema está en línea", bg=COLORES["fondo"], fg=COLORES["verde"],
                 font=("Segoe UI", 9)).grid(row=9, column=0, sticky="w", padx=22, pady=(0, 9))
        tk.Label(sidebar, text="LOGÍSTICA INTELIGENTE  ·  v1.0", bg=COLORES["fondo"], fg="#675B75",
                 font=("Segoe UI", 7, "bold")).grid(row=10, column=0, sticky="w", padx=22, pady=(0, 20))

    def _crear_kpis(self):
        self.fila_kpis = tk.Frame(self.contenido, bg=COLORES["noche"])
        self.fila_kpis.grid(row=2, column=0, sticky="ew", padx=28)
        for columna in range(4):
            self.fila_kpis.grid_columnconfigure(columna, weight=1, uniform="kpi")
        self.kpi_valores = {}
        datos = [("camiones", "CAMIONES REGISTRADOS", "0", "🚚", COLORES["neon"]),
                 ("accesos", "ACCESOS EVALUADOS", "0", "◈", COLORES["verde"]),
                 ("incidentes", "INCIDENTES DETECTADOS", "0", "✉", COLORES["naranja"]),
                 ("riesgo", "PUNTAJE DE RIESGO", "16 / 25", "🎃", COLORES["rojo"])]
        for columna, (clave, etiqueta, valor, icono, acento) in enumerate(datos):
            tarjeta = self._panel(self.fila_kpis)
            tarjeta.grid(row=0, column=columna, sticky="ew", padx=(0 if columna == 0 else 7, 7), pady=3)
            tarjeta.grid_columnconfigure(0, weight=1)
            tk.Label(tarjeta, text=etiqueta, bg=COLORES["panel"], fg=COLORES["suave"],
                     font=("Segoe UI", 8, "bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=14, pady=(13, 4))
            valor_lbl = tk.Label(tarjeta, text=valor, bg=COLORES["panel"], fg=COLORES["texto"],
                                 font=("Segoe UI Semibold", 20), anchor="w")
            valor_lbl.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))
            self.kpi_valores[clave] = valor_lbl
            tk.Label(tarjeta, text=icono, bg=COLORES["panel"], fg=acento,
                     font=("Segoe UI Emoji", 20)).grid(row=0, column=1, rowspan=2, padx=13)

    @staticmethod
    def _panel(parent):
        return tk.Frame(parent, bg=COLORES["panel"], highlightbackground=COLORES["borde"],
                        highlightthickness=1, bd=0)

    def _encabezado_panel(self, parent, texto, detalle=None, icono=None):
        fila = tk.Frame(parent, bg=COLORES["panel"])
        fila.pack(fill="x", padx=18, pady=(16, 11))
        titulo = f"{icono}  {texto}" if icono else texto
        tk.Label(fila, text=titulo, bg=COLORES["panel"], fg=COLORES["texto"],
                 font=("Segoe UI Semibold", 12), anchor="w").pack(anchor="w")
        if detalle:
            tk.Label(fila, text=detalle, bg=COLORES["panel"], fg=COLORES["suave"],
                     font=("Segoe UI", 9), anchor="w").pack(anchor="w", pady=(4, 0))

    def _campo(self, parent, etiqueta, ancho=None):
        bloque = tk.Frame(parent, bg=COLORES["panel"])
        tk.Label(bloque, text=etiqueta.upper(), bg=COLORES["panel"], fg=COLORES["suave"],
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
        entrada = tk.Entry(bloque, width=ancho, bg=COLORES["entrada"], fg=COLORES["texto"],
                           insertbackground=COLORES["naranja"], relief="flat", highlightthickness=1,
                           highlightbackground=COLORES["borde"], highlightcolor=COLORES["naranja"],
                           font=("Segoe UI", 10))
        entrada.pack(fill="x", ipady=9)
        return bloque, entrada

    def _boton(self, parent, texto, comando, primario=True):
        fondo = COLORES["naranja"] if primario else COLORES["borde"]
        frente = COLORES["fondo"] if primario else COLORES["texto"]
        return tk.Button(parent, text=texto, command=comando, bg=fondo, fg=frente,
                         activebackground=COLORES["neon"] if primario else COLORES["panel"],
                         activeforeground=COLORES["texto"], relief="flat", bd=0,
                         font=("Segoe UI Semibold", 9), padx=16, pady=10, cursor="hand2")

    def _mostrar_vista(self, clave):
        nombre, subtitulo = self.VISTAS[clave]
        self.lbl_titulo_vista.config(text=nombre)
        self.lbl_subtitulo_vista.config(text=subtitulo)
        self.vistas[clave].tkraise()
        if clave == "riesgos" and hasattr(self, "tabla_riesgos"):
            self._cargar_tabla_riesgos()
        for nav, boton in self.botones_nav.items():
            seleccionado = nav == clave
            boton.config(bg=COLORES["panel"] if seleccionado else COLORES["fondo"],
                         fg=COLORES["naranja"] if seleccionado else COLORES["suave"],
                         font=("Segoe UI Semibold" if seleccionado else "Segoe UI", 10))

    def _actualizar_kpis(self):
        for coleccion, clave in (("camiones", "camiones"), ("accesos", "accesos"), ("incidentes", "incidentes")):
            try:
                self.kpi_valores[clave].config(text=str(self.db.contar(coleccion)))
            except Exception:
                self.kpi_valores[clave].config(text="—")
        try:
            riesgos = self._datos_riesgos()
            puntaje = max((r["puntaje_inicial"] for r in riesgos), default=0)
            self.kpi_valores["riesgo"].config(text=f"{puntaje} / 25")
        except Exception as exc:
            log.exception("No se pudieron cargar los riesgos para el indicador")
            self.kpi_valores["riesgo"].config(text="—")
            if hasattr(self, "lbl_estado_riesgos"):
                self.lbl_estado_riesgos.config(text=f"No se pudieron cargar riesgos: {exc}")

    def _crear_vista_acceso(self, vista):
        vista.grid_columnconfigure(0, weight=3)
        vista.grid_columnconfigure(1, weight=2)
        vista.grid_rowconfigure(0, weight=1)
        panel_eval = self._panel(vista)
        panel_eval.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel_camiones = self._panel(vista)
        panel_camiones.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._encabezado_panel(panel_eval, "Evaluar ingreso", "Las reglas combinan autorización, carga y certificación.", "◈")
        form = tk.Frame(panel_eval, bg=COLORES["panel"])
        form.pack(fill="x", padx=18, pady=(4, 14))
        bloque, self.ent_placa = self._campo(form, "Placa del vehículo")
        bloque.pack(fill="x", pady=(0, 12))
        self.ent_placa.insert(0, "CAM-101")
        self._boton(form, "Evaluar acceso   →", self._evaluar_acceso).pack(anchor="w")
        self.lbl_resultado_acceso = tk.Label(panel_eval, text="ESPERANDO CONSULTA", bg=COLORES["panel"],
                                             fg=COLORES["suave"], font=("Segoe UI Semibold", 11), anchor="w")
        self.lbl_resultado_acceso.pack(fill="x", padx=18, pady=(10, 7))
        self.txt_explicacion_acceso = scrolledtext.ScrolledText(
            panel_eval, height=11, bg=COLORES["entrada"], fg=COLORES["suave"],
            insertbackground=COLORES["naranja"], relief="flat", font=("Consolas", 9), wrap="word", padx=12, pady=10)
        self.txt_explicacion_acceso.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self.txt_explicacion_acceso.insert("end", "Selecciona una placa y ejecuta la evaluación.")
        self.txt_explicacion_acceso.configure(state="disabled")
        self._encabezado_panel(panel_camiones, "Flota reciente", "Vehículos registrados", "🚚")
        self.tabla_camiones = self._crear_tabla(panel_camiones, ("placa", "empresa", "tipo_carga"),
                                                ("Placa", "Empresa", "Carga"))
        self.tabla_camiones.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self._actualizar_tabla_camiones()

    def _evaluar_acceso(self):
        placa = self.ent_placa.get().strip().upper()
        if not placa:
            messagebox.showwarning("LogiSmart", "Escribe una placa para evaluar el acceso.")
            return
        try:
            camiones = self.db.listar("camiones", filtro={"placa": placa}, limite=1)
        except Exception as exc:
            messagebox.showerror("MongoDB", str(exc))
            return
        camion = camiones[0] if camiones else None
        p = camion.get("autorizacion", True) if camion else True
        q = camion.get("lista_negra", False) if camion else False
        r = camion.get("documentos_incompletos", False) if camion else False
        s = camion.get("certificacion_valida", True) if camion else True
        resultado = evaluar_reglas(P=p, Q=q, R=r, S=s)
        estados = {"ACCESO_ESTANDAR": ("✓  ACCESO ESTÁNDAR", COLORES["verde"]),
                   "INSPECCION_ESPECIAL": ("⚠  INSPECCIÓN ESPECIAL", COLORES["naranja"]),
                   "DENEGADO": ("✕  ACCESO DENEGADO", COLORES["rojo"])}
        texto, color = estados[resultado["decision"]]
        self.lbl_resultado_acceso.config(text=f"{texto}  ·  {placa}", fg=color)
        self.txt_explicacion_acceso.configure(state="normal")
        self.txt_explicacion_acceso.delete("1.0", "end")
        nombre = camion.get("empresa", "Vehículo") if camion else "Vehículo no registrado"
        self.txt_explicacion_acceso.insert("end", f"{nombre}\nPremisas: P={p}, Q={q}, R={r}, S={s}\n\n")
        self.txt_explicacion_acceso.insert("end", "\n".join(resultado["explicacion"]))
        self.txt_explicacion_acceso.configure(state="disabled")
        momento = ahora()
        try:
            self.db.insertar("accesos", {
                "fecha": momento,
                "placa": placa,
                "camion_id": (
                    camion.get("camion_id", camion.get("_id")) if camion else None
                ),
                "decision": resultado["decision"],
                "premisas": {"P": p, "Q": q, "R": r, "S": s},
                "empresa": camion.get("empresa") if camion else None,
                "tipo_carga": camion.get("tipo_carga") if camion else None,
                "documentos_incompletos": r,
                "certificacion_valida": s,
                "autorizacion": p,
                "lista_negra": q,
                "timestamp_entrada": (
                    momento if resultado["decision"] != "DENEGADO" else None
                ),
            })
        except Exception as exc:
            messagebox.showerror("Registro de acceso", str(exc))
        self._actualizar_kpis()

    def _crear_vista_clasificador(self, vista):
        vista.grid_columnconfigure(0, weight=1)
        vista.grid_columnconfigure(1, weight=1)
        vista.grid_rowconfigure(0, weight=1)
        panel_entrada, panel_resultado = self._panel(vista), self._panel(vista)
        panel_entrada.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        panel_resultado.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self._encabezado_panel(panel_entrada, "Correo recibido", "Pega el reporte del operador para clasificarlo.", "✉")
        self.txt_correo_input = scrolledtext.ScrolledText(
            panel_entrada, height=12, bg=COLORES["entrada"], fg=COLORES["texto"],
            insertbackground=COLORES["naranja"], relief="flat", font=("Segoe UI", 10), wrap="word", padx=12, pady=12)
        self.txt_correo_input.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.txt_correo_input.insert("end", "Reportamos un derrame de líquido hidráulico en la puerta 4. CAM-101 está detenido.")
        self._boton(panel_entrada, "Clasificar incidente   →", self._clasificar_correo).pack(anchor="w", padx=18, pady=(0, 18))
        self._encabezado_panel(panel_resultado, "Resultado del análisis", "La prioridad se resalta según la gravedad.", "✦")
        self.lbl_badges_incidente = tk.Frame(panel_resultado, bg=COLORES["panel"])
        self.lbl_badges_incidente.pack(fill="x", padx=18, pady=(4, 12))
        self.txt_clasificacion_out = scrolledtext.ScrolledText(
            panel_resultado, height=12, bg=COLORES["entrada"], fg=COLORES["texto"],
            insertbackground=COLORES["naranja"], relief="flat", font=("Segoe UI", 10), wrap="word", padx=12, pady=12)
        self.txt_clasificacion_out.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.txt_clasificacion_out.insert("end", "El resultado aparecerá aquí.")

    def _clasificar_correo(self):
        texto = self.txt_correo_input.get("1.0", "end").strip()
        if not texto:
            return
        resultado = self.clasificador.clasificar_correo(texto)
        try:
            cfg_ollama = {
                clave: self.clasificador.cfg[clave]
                for clave in ("ollama_host", "modelo", "modo_clasificacion", "reintentos", "timeout_llm")
                if clave in self.clasificador.cfg
            }
            self.db.insertar("incidentes", {
                "fecha": ahora(),
                "correo": texto,
                "correo_original": texto,
                "resultado": resultado,
                "clasificacion": resultado,
                "configuracion_ollama": cfg_ollama,
            })
        except Exception as exc:
            messagebox.showerror("Registro de incidente", str(exc))
        for widget in self.lbl_badges_incidente.winfo_children():
            widget.destroy()
        prioridad = resultado.get("prioridad", "Baja")
        color = {"Alta": COLORES["rojo"], "Media": COLORES["naranja"],
                 "Baja": COLORES["verde"]}.get(prioridad, COLORES["neon"])
        self._badge(self.lbl_badges_incidente, resultado.get("categoria", "Otro"), COLORES["neon"])
        self._badge(self.lbl_badges_incidente, f"Prioridad {prioridad}", color)
        self.txt_clasificacion_out.delete("1.0", "end")
        self.txt_clasificacion_out.insert("end", f"Resumen\n{resultado.get('resumen', '')}\n\n"
                                           f"Entidades\n{', '.join(resultado.get('entidades', [])) or 'Sin entidades detectadas'}\n\n"
                                           f"Método\n{resultado.get('metodo', 'No especificado')}")
        self._actualizar_kpis()

    @staticmethod
    def _badge(parent, texto, color):
        tk.Label(parent, text=texto.upper(), bg=color, fg=COLORES["fondo"],
                 font=("Segoe UI", 8, "bold"), padx=10, pady=6).pack(side="left", padx=(0, 7))

    def _crear_vista_asistente(self, vista):
        panel = self._panel(vista)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        cabecera = tk.Frame(panel, bg=COLORES["panel"])
        cabecera.grid(row=0, column=0, sticky="ew", padx=18, pady=(15, 10))
        tk.Label(cabecera, text="🐈‍⬛", bg=COLORES["panel"], fg=COLORES["neon"],
                 font=("Segoe UI Emoji", 26)).pack(side="left", padx=(0, 12))
        identidad = tk.Frame(cabecera, bg=COLORES["panel"])
        identidad.pack(side="left")
        tk.Label(identidad, text="Familiar de LogiSmart", bg=COLORES["panel"], fg=COLORES["texto"],
                 font=("Segoe UI Semibold", 11)).pack(anchor="w")
        tk.Label(identidad, text=f"OLLAMA  ·  {self.cfg.get('modelo', 'llama3.2')}",
                 bg=COLORES["panel"], fg=COLORES["neon"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.txt_chat_historial = scrolledtext.ScrolledText(
            panel, height=12, bg=COLORES["entrada"], fg=COLORES["texto"], insertbackground=COLORES["naranja"],
            relief="flat", font=("Segoe UI", 10), wrap="word", padx=15, pady=14)
        self.txt_chat_historial.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 14))
        self.txt_chat_historial.tag_configure("operador", foreground=COLORES["naranja"], font=("Segoe UI Semibold", 10))
        self.txt_chat_historial.tag_configure("asistente", foreground=COLORES["neon"], font=("Segoe UI Semibold", 10))
        entrada_fila = tk.Frame(panel, bg=COLORES["panel"])
        entrada_fila.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        entrada_fila.grid_columnconfigure(0, weight=1)
        self.ent_pregunta = tk.Entry(entrada_fila, bg=COLORES["entrada"], fg=COLORES["texto"],
                                     insertbackground=COLORES["naranja"], relief="flat", highlightthickness=1,
                                     highlightbackground=COLORES["borde"], font=("Segoe UI", 10))
        self.ent_pregunta.grid(row=0, column=0, sticky="ew", padx=(0, 10), ipady=11)
        self.ent_pregunta.bind("<Return>", lambda _event: self._enviar_pregunta_rag())
        self._boton(entrada_fila, "Preguntar a Ollama  →", self._enviar_pregunta_rag).grid(row=0, column=1)

    def _enviar_pregunta_rag(self):
        pregunta = self.ent_pregunta.get().strip()
        if not pregunta:
            return
        self.txt_chat_historial.insert("end", f"TÚ\n{pregunta}\n\n", "operador")
        self.ent_pregunta.delete(0, "end")
        self.txt_chat_historial.insert("end", "FAMILIAR · OLLAMA\n", "asistente")
        self.txt_chat_historial.insert("end", "Consultando…\n\n")
        self.txt_chat_historial.see("end")
        self.root.update_idletasks()
        respuesta = self.asistente.responder_pregunta(pregunta)
        self.txt_chat_historial.delete("end-3l", "end")
        self.txt_chat_historial.insert("end", f"FAMILIAR · OLLAMA\n{respuesta}\n\n", "asistente")
        self.txt_chat_historial.see("end")

    def _crear_vista_riesgos(self, vista):
        panel = self._panel(vista)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        self._encabezado_panel(panel, "Registro de riesgos", "Matriz 5 × 5 · mitigación y exposición residual", "⚗")
        acciones = tk.Frame(panel, bg=COLORES["panel"])
        acciones.pack(fill="x", padx=16, pady=(0, 10))
        self._boton(acciones, "Nuevo riesgo", self._nuevo_riesgo).pack(side="left", padx=(0, 8))
        self._boton(acciones, "Editar seleccionado", self._editar_riesgo, primario=False).pack(
            side="left", padx=(0, 8)
        )
        self._boton(acciones, "Eliminar seleccionado", self._eliminar_riesgo, primario=False).pack(
            side="left"
        )
        self.lbl_estado_riesgos = tk.Label(
            panel,
            text="",
            bg=COLORES["panel"],
            fg=COLORES["suave"],
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_estado_riesgos.pack(fill="x", padx=18, pady=(0, 8))
        columnas = ("modulo", "descripcion", "inicial", "mitigacion", "residual")
        titulos = ("Módulo", "Descripción", "Nivel inicial", "Mitigación", "Nivel residual")
        self.tabla_riesgos = self._crear_tabla(panel, columnas, titulos)
        self.tabla_riesgos.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.tabla_riesgos.tag_configure("critico", foreground=COLORES["rojo"])
        self.tabla_riesgos.tag_configure("alto", foreground=COLORES["naranja"])
        self.tabla_riesgos.tag_configure("medio", foreground=COLORES["amarillo"])
        self._cargar_tabla_riesgos()

    def _crear_tabla(self, parent, columnas, titulos):
        tabla = ttk.Treeview(parent, columns=columnas, show="headings", style="Logi.Treeview")
        anchos = (120, 210, 145, 290, 145) if len(columnas) == 5 else (105, 150, 120)
        for columna, titulo, ancho in zip(columnas, titulos, anchos):
            tabla.heading(columna, text=titulo)
            tabla.column(columna, width=ancho, minwidth=80, anchor="w", stretch=True)
        return tabla

    def _datos_riesgos(self):
        riesgos = self.db.listar("riesgos_eticos")
        return [self.evaluador_riesgos.procesar_riesgo(riesgo) for riesgo in riesgos]

    def _cargar_tabla_riesgos(self):
        self.tabla_riesgos.delete(*self.tabla_riesgos.get_children())
        try:
            riesgos = self._datos_riesgos()
        except Exception as exc:
            log.exception("No se pudo cargar la matriz de riesgos")
            self.lbl_estado_riesgos.config(
                text=f"No se pudieron cargar riesgos. Revisa la conexión a MongoDB: {exc}",
                fg=COLORES["rojo"],
            )
            return
        if not riesgos:
            self.lbl_estado_riesgos.config(
                text="No hay riesgos registrados. Usa «Nuevo riesgo» para agregar el primero.",
                fg=COLORES["amarillo"],
            )
            return
        self.lbl_estado_riesgos.config(
            text=f"{len(riesgos)} riesgo(s) cargado(s) desde riesgos_eticos.",
            fg=COLORES["verde"],
        )
        for procesado in riesgos:
            nivel = procesado["nivel_inicial"].lower()
            tag = "critico" if nivel == "crítico" else nivel if nivel in ("alto", "medio") else ""
            icono = "🧙" if nivel in ("alto", "crítico") else "🧪"
            self.tabla_riesgos.insert(
                "",
                "end",
                iid=str(procesado["_id"]),
                values=(
                    procesado.get("modulo", "—"),
                    procesado.get("descripcion", "—"),
                    f"{icono} {procesado['nivel_inicial']} · {procesado['puntaje_inicial']}/25",
                    procesado.get("mitigacion", "—"),
                    f"{procesado['nivel_residual']} · {procesado['puntaje_residual']}/25",
                ),
                tags=(tag,),
            )

    def _formulario_riesgo(self, riesgo=None):
        editar = riesgo is not None
        ventana = tk.Toplevel(self.root)
        ventana.title("Editar riesgo" if editar else "Nuevo riesgo")
        ventana.configure(bg=COLORES["panel"])
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.resizable(False, False)
        ventana.grid_columnconfigure(1, weight=1)

        campos_texto = (
            ("modulo", "Módulo"),
            ("descripcion", "Descripción"),
            ("mitigacion", "Mitigación"),
        )
        entradas = {}
        for fila, (clave, etiqueta) in enumerate(campos_texto):
            tk.Label(
                ventana,
                text=etiqueta,
                bg=COLORES["panel"],
                fg=COLORES["texto"],
                font=("Segoe UI", 9),
            ).grid(row=fila, column=0, sticky="w", padx=14, pady=7)
            entrada = tk.Entry(
                ventana,
                bg=COLORES["entrada"],
                fg=COLORES["texto"],
                insertbackground=COLORES["naranja"],
                relief="flat",
                width=48,
            )
            entrada.grid(row=fila, column=1, sticky="ew", padx=14, pady=7, ipady=6)
            entrada.insert(0, str((riesgo or {}).get(clave, "")))
            entradas[clave] = entrada

        campos_puntaje = (
            ("probabilidad_inicial", "Probabilidad inicial"),
            ("impacto_inicial", "Impacto inicial"),
            ("probabilidad_residual", "Probabilidad residual"),
            ("impacto_residual", "Impacto residual"),
        )
        for indice, (clave, etiqueta) in enumerate(campos_puntaje, start=len(campos_texto)):
            tk.Label(
                ventana,
                text=etiqueta,
                bg=COLORES["panel"],
                fg=COLORES["texto"],
                font=("Segoe UI", 9),
            ).grid(row=indice, column=0, sticky="w", padx=14, pady=7)
            selector = ttk.Combobox(ventana, values=("1", "2", "3", "4", "5"), state="readonly", width=8)
            selector.grid(row=indice, column=1, sticky="w", padx=14, pady=7)
            valor = (riesgo or {}).get(clave, 1)
            selector.set(str(valor))
            entradas[clave] = selector

        def guardar():
            cambios = {
                clave: entrada.get().strip()
                for clave, entrada in entradas.items()
                if clave in {"modulo", "descripcion", "mitigacion"}
            }
            if any(not valor for valor in cambios.values()):
                messagebox.showwarning(
                    "Matriz de riesgos",
                    "Completa el módulo, la descripción y la mitigación.",
                    parent=ventana,
                )
                return
            cambios.update({
                clave: int(entradas[clave].get())
                for clave, _etiqueta in campos_puntaje
            })
            try:
                self.evaluador_riesgos.procesar_riesgo(cambios)
                if editar:
                    if not self.db.actualizar("riesgos_eticos", str(riesgo["_id"]), cambios=cambios):
                        raise ValueError("El riesgo ya no existe en la base de datos.")
                else:
                    cambios["creado_en"] = ahora()
                    self.db.insertar("riesgos_eticos", cambios)
            except Exception as exc:
                log.exception("No se pudo guardar el riesgo")
                messagebox.showerror("Matriz de riesgos", str(exc), parent=ventana)
                return
            ventana.destroy()
            self._cargar_tabla_riesgos()
            self._actualizar_kpis()

        botones = tk.Frame(ventana, bg=COLORES["panel"])
        botones.grid(row=len(campos_texto) + len(campos_puntaje), column=0, columnspan=2, pady=14)
        self._boton(botones, "Guardar", guardar).pack(side="left", padx=6)
        self._boton(botones, "Cancelar", ventana.destroy, primario=False).pack(side="left", padx=6)
        ventana.wait_window()

    def _nuevo_riesgo(self):
        self._formulario_riesgo()

    def _riesgo_seleccionado(self):
        seleccion = self.tabla_riesgos.selection()
        if not seleccion:
            messagebox.showwarning("Matriz de riesgos", "Selecciona un riesgo de la tabla.")
            return None
        try:
            riesgo = self.db.obtener("riesgos_eticos", seleccion[0])
        except Exception as exc:
            log.exception("No se pudo leer el riesgo seleccionado")
            messagebox.showerror("Matriz de riesgos", str(exc))
            return None
        if riesgo is None:
            messagebox.showerror("Matriz de riesgos", "El riesgo seleccionado ya no existe.")
        return riesgo

    def _editar_riesgo(self):
        riesgo = self._riesgo_seleccionado()
        if riesgo is not None:
            self._formulario_riesgo(riesgo)

    def _eliminar_riesgo(self):
        riesgo = self._riesgo_seleccionado()
        if riesgo is None:
            return
        if not messagebox.askyesno(
            "Eliminar riesgo",
            f"¿Eliminar el riesgo «{riesgo.get('modulo', 'sin módulo')}»?",
        ):
            return
        try:
            if not self.db.eliminar("riesgos_eticos", str(riesgo["_id"])):
                raise ValueError("El riesgo ya no existe en la base de datos.")
        except Exception as exc:
            log.exception("No se pudo eliminar el riesgo")
            messagebox.showerror("Matriz de riesgos", str(exc))
            return
        self._cargar_tabla_riesgos()
        self._actualizar_kpis()

    def _crear_vista_reportes(self, vista):
        panel = self._panel(vista)
        panel.grid(row=0, column=0, sticky="nsew")
        self._encabezado_panel(
            panel,
            "Exportar reportes",
            "Selecciona un formato y elige dónde guardar el archivo.",
            "▤",
        )
        opciones = (
            (
                "Bitácora de accesos · CSV",
                "Camiones, permisos, estatus documental y marcas de tiempo.",
                "csv",
                exportar_csv,
            ),
            (
                "Análisis y riesgos · JSON",
                "Incidentes, evaluaciones LLM y riesgos éticos en estructura completa.",
                "json",
                exportar_json,
            ),
            (
                "Informe ejecutivo · PDF",
                "Resumen ISO semanal y alertas críticas con puntaje desde 17.",
                "pdf",
                exportar_pdf,
            ),
        )
        for titulo, detalle, extension, exportador in opciones:
            fila = tk.Frame(panel, bg=COLORES["panel"])
            fila.pack(fill="x", padx=20, pady=9)
            texto = tk.Frame(fila, bg=COLORES["panel"])
            texto.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Label(
                texto, text=titulo, bg=COLORES["panel"], fg=COLORES["texto"],
                font=("Segoe UI Semibold", 10), anchor="w",
            ).pack(fill="x")
            tk.Label(
                texto, text=detalle, bg=COLORES["panel"], fg=COLORES["suave"],
                font=("Segoe UI", 9), anchor="w", wraplength=600, justify="left",
            ).pack(fill="x", pady=(4, 0))
            self._boton(
                fila,
                f"Exportar .{extension}",
                lambda ext=extension, func=exportador: self._exportar_reporte(ext, func),
            ).pack(side="right")

    def _exportar_reporte(self, extension, exportador):
        ruta = filedialog.asksaveasfilename(
            title=f"Guardar reporte {extension.upper()}",
            initialdir=Path(__file__).resolve().parents[1] / "reportes",
            initialfile=f"reporte_logismart.{extension}",
            defaultextension=f".{extension}",
            filetypes=[(f"Archivo {extension.upper()}", f"*.{extension}")],
        )
        if not ruta:
            return
        try:
            total = exportador(self.db, ruta)
        except Exception as exc:
            log.exception("No se pudo exportar el reporte %s", extension.upper())
            messagebox.showerror("Error al exportar", str(exc))
            return
        messagebox.showinfo(
            "Reporte exportado",
            f"Archivo guardado correctamente.\nRegistros incluidos: {total}",
        )

    def _actualizar_tabla_camiones(self):
        self.tabla_camiones.delete(*self.tabla_camiones.get_children())
        try:
            camiones = self.db.listar("camiones", limite=8)
        except Exception:
            camiones = []
        for camion in camiones:
            self.tabla_camiones.insert("", "end", values=(
                camion.get("placa", "—"), camion.get("empresa", "—"), camion.get("tipo_carga", "—")))

    def _crear_vista_configuracion(self, vista):
        panel = self._panel(vista)
        panel.grid(row=0, column=0, sticky="nsew")
        self._encabezado_panel(panel, "Conexiones del sistema", "Los cambios se guardan en logismart_config.json.", "⚙")
        cuerpo = tk.Frame(panel, bg=COLORES["panel"])
        cuerpo.pack(fill="x", padx=20, pady=(8, 16))
        cuerpo.grid_columnconfigure(0, weight=1)
        self.config_campos = {}
        campos = (("mongo_uri", "MongoDB URI"), ("mongo_db", "Base de datos"),
                  ("ollama_host", "Servidor Ollama"), ("modelo", "Modelo local"))
        for fila, (clave, etiqueta) in enumerate(campos):
            bloque, entrada = self._campo(cuerpo, etiqueta)
            bloque.grid(row=fila, column=0, sticky="ew", pady=(0, 13))
            entrada.insert(0, str(self.cfg.get(clave, "")))
            self.config_campos[clave] = entrada
        estado_db = self.db.error if not self.db.conectado else ""
        self.lbl_config_estado = tk.Label(panel, text=estado_db, bg=COLORES["panel"],
                                          fg=COLORES["rojo"] if estado_db else COLORES["suave"],
                                          font=("Segoe UI", 9), anchor="w")
        self.lbl_config_estado.pack(fill="x", padx=20, pady=(0, 10))
        self._boton(panel, "Guardar y reconectar   →", self._guardar_configuracion).pack(
            anchor="w", padx=20, pady=(0, 20))

    def _guardar_configuracion(self):
        for clave, entrada in self.config_campos.items():
            valor = entrada.get().strip()
            if not valor:
                messagebox.showwarning("Configuración", f"El campo {clave} no puede estar vacío.")
                return
            self.cfg[clave] = valor
        try:
            guardar_config(self.cfg)
            self.db.cerrar()
            self.db = self._crear_db()
            conectado = self.db.conectar()
            self.clasificador = ClasificadorHibrido()
            self.asistente = AsistenteRAG(self.db)
            color = COLORES["verde"] if conectado else COLORES["rojo"]
            estado = "Configuración guardada · MongoDB conectado" if conectado else (
                f"Guardada, pero MongoDB no conecta: {self.db.error}")
            self.lbl_config_estado.config(text=estado, fg=color)
            estado_db = "MongoDB conectado" if conectado else "MongoDB desconectado"
            self.lbl_estado_db.config(text=f"●  {estado_db}",
                                      fg=COLORES["verde"] if conectado else COLORES["rojo"])
            self.lbl_modelo.config(text=f"✦  {self.cfg['modelo']}")
            self._actualizar_kpis()
            self._actualizar_tabla_camiones()
        except Exception as exc:
            self.lbl_config_estado.config(text=f"No se pudo guardar: {exc}", fg=COLORES["rojo"])