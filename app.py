# -*- coding: utf-8 -*-
"""Punto de entrada principal para ejecutar la aplicación LogiSmart."""
import tkinter as tk
from gui.main_window import VentanaPrincipal
from utils import log


def main():
    log.info("Iniciando aplicación LogiSmart...")
    root = tk.Tk()
    app = VentanaPrincipal(root)
    root.mainloop()


if __name__ == "__main__":
    main()