# -*- coding: utf-8 -*-
"""Herramientas para datos de demostración."""


def cargar_datos_demostracion():
	from datos_demo.semilla import cargar_datos_demostracion as cargar

	return cargar()


__all__ = ["cargar_datos_demostracion"]