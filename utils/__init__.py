#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utils Package - Utilidades para M3U8 Downloader
==============================================

Paquete de utilidades para organizar mejor el código y reducir
la complejidad del archivo principal app.py.

Módulos disponibles:
- progress_manager: Gestión centralizada de progreso
- file_handler: Manejo de archivos y metadatos
- response_helper: Helpers para respuestas HTTP/JSON
- validation: Validación de URLs y datos

Autor: M3U8 Downloader System
"""

from .progress_manager import ProgressManager, progress_manager, create_progress_callback

__all__ = [
    'ProgressManager', 
    'progress_manager', 
    'create_progress_callback'
]