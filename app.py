import threading
import uuid
import re
import os
import glob
import time
from flask import Flask, render_template_string, request, send_file, jsonify
from test import M3U8Downloader

# Configuración de la aplicación
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia esto por una clave segura en producción

# Variables globales para el control de descargas
multi_progress = {}
cancelled_downloads = set()
download_queue_storage = []  # Cola persistente
queue_running = False

# Configuración
MAX_CONCURRENT_DOWNLOADS = 5
STATIC_DIR = 'static'
TEMP_DIR = 'temp_segments'
DEFAULT_QUALITY = 'best'  # best, 1080p, 720p, 480p

# Funciones para persistencia
def save_download_state():
    """Guarda el estado de las descargas en un archivo JSON"""
    import json
    try:
        state = {
            'multi_progress': multi_progress,
            'download_queue': download_queue_storage,
            'queue_running': queue_running
        }
        with open('download_state.json', 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error guardando estado: {e}")

def load_download_state():
    """Carga el estado de las descargas desde un archivo JSON"""
    import json
    global multi_progress, download_queue_storage, queue_running
    try:
        if os.path.exists('download_state.json'):
            with open('download_state.json', 'r', encoding='utf-8') as f:
                state = json.load(f)
                multi_progress = state.get('multi_progress', {})
                download_queue_storage = state.get('download_queue', [])
                queue_running = state.get('queue_running', False)
                
                # Limpiar descargas que ya no están activas
                active_downloads = {}
                for download_id, progress in multi_progress.items():
                    if progress['status'] == 'downloading':
                        # Marcar como pausada si estaba descargando
                        progress['status'] = 'paused'
                        progress['can_resume'] = True
                    active_downloads[download_id] = progress
                multi_progress = active_downloads
                
                print(f"Estado cargado: {len(multi_progress)} descargas, {len(download_queue_storage)} en cola")
    except Exception as e:
        print(f"Error cargando estado: {e}")

# Cargar estado al iniciar
load_download_state()

default_html = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargador M3U8 Mejorado</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><defs><linearGradient id='bg' x1='0%25' y1='0%25' x2='100%25' y2='100%25'><stop offset='0%25' stop-color='%23667eea'/><stop offset='100%25' stop-color='%23764ba2'/></linearGradient></defs><rect width='32' height='32' rx='6' fill='url(%23bg)'/><rect x='6' y='9' width='20' height='14' rx='2' fill='white' fill-opacity='0.95'/><rect x='7.5' y='10.5' width='17' height='11' rx='1' fill='%23212529'/><polygon points='12.5,14.5 18,17 12.5,19.5' fill='%23667eea'/><circle cx='24' cy='24' r='6' fill='%2328a745'/><path d='M21,24 L23,26 L27,22' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/></svg>">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        /* Variables CSS para consistencia */
        :root {
            --primary-color: #667eea;
            --primary-dark: #5a67d8;
            --secondary-color: #764ba2;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --error-color: #dc3545;
            --info-color: #17a2b8;
            --dark-color: #212529;
            --light-color: #f8f9fa;
            --border-radius: 0.75rem;
            --border-radius-sm: 0.5rem;
            --box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --box-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* Diseño base mejorado */
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: #fff; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            min-height: 100vh;
        }

        /* Sidebar moderna con glassmorphism */
        .sidebar { 
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-right: 1px solid rgba(255, 255, 255, 0.2);
            min-height: 100vh; 
            padding: 2rem 1.5rem;
            box-shadow: var(--box-shadow-lg);
        }
        
        .sidebar h3 { 
            color: #fff; 
            font-weight: 600;
            margin-bottom: 1.5rem;
            font-size: 1.25rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
            padding-bottom: 0.5rem;
        }
        
        .sidebar ul { list-style: none; padding: 0; margin: 0; }
        
        .sidebar li { 
            background: rgba(255, 255, 255, 0.08);
            padding: 1rem;
            border-radius: var(--border-radius-sm);
            margin-bottom: 0.75rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }
        
        .sidebar li:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
            box-shadow: var(--box-shadow);
        }
        
        .sidebar a { 
            color: #e2e8f0; 
            text-decoration: none; 
            font-weight: 500;
            display: block;
        }
        
        .sidebar a:hover { 
            color: #fff;
            text-decoration: none;
        }

        /* Área principal con mejor espaciado */
        .main { 
            padding: 2.5rem; 
            background: rgba(255, 255, 255, 0.05);
            border-radius: var(--border-radius) 0 0 var(--border-radius);
            margin-left: -15px;
        }

        /* Títulos con mejor jerarquía */
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #fff 0%, #e2e8f0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Formulario mejorado */
        .form-container {
            background: rgba(255, 255, 255, 0.1);
            padding: 2rem;
            border-radius: var(--border-radius);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 2rem;
            box-shadow: var(--box-shadow);
        }

        .form-control {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid transparent !important;
            border-radius: var(--border-radius-sm) !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            transition: var(--transition) !important;
            color: var(--dark-color) !important;
        }

        .form-control:focus {
            background: rgba(255, 255, 255, 1) !important;
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
            transform: translateY(-1px);
        }

        .form-control::placeholder {
            color: #6b7280 !important;
            opacity: 1 !important;
        }

        /* Botones modernos */
        .btn {
            border-radius: var(--border-radius-sm) !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            transition: var(--transition) !important;
            border: none !important;
            position: relative;
            overflow: hidden;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: var(--box-shadow);
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%) !important;
        }

        .btn-success {
            background: linear-gradient(135deg, var(--success-color) 0%, #22c55e 100%) !important;
        }

        .btn-info {
            background: linear-gradient(135deg, var(--info-color) 0%, #06b6d4 100%) !important;
        }

        .btn-warning {
            background: linear-gradient(135deg, var(--warning-color) 0%, #f59e0b 100%) !important;
            color: var(--dark-color) !important;
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--error-color) 0%, #ef4444 100%) !important;
        }

        /* Cards para descargas */
        .descarga-item { 
            background: rgba(255, 255, 255, 0.1);
            padding: 1.5rem; 
            margin-bottom: 1rem; 
            border-radius: var(--border-radius);
            border-left: 4px solid var(--primary-color);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: var(--transition);
            position: relative;
            overflow: hidden;
        }

        .descarga-item:hover {
            transform: translateY(-2px);
            box-shadow: var(--box-shadow-lg);
        }

        .descarga-cancelled { border-left-color: var(--warning-color) !important; }
        .descarga-error { border-left-color: var(--error-color) !important; }
        .descarga-done { border-left-color: var(--success-color) !important; }

        /* Estilos responsivos para descargas activas */
        .descarga-item .text-truncate {
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .descarga-item .btn-group-responsive {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            justify-content: flex-end;
            align-items: center;
        }

        .descarga-item .btn-sm {
            min-width: 35px;
            height: 32px;
            padding: 0.25rem 0.5rem;
            font-size: 0.875rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Mejorar URL display */
        .url-display {
            word-break: break-all;
            font-size: 0.75rem !important;
            line-height: 1.2;
            max-height: 60px;
            overflow-y: auto;
        }

        /* Información de descarga compacta */
        .download-stats {
            font-size: 0.8rem;
            opacity: 0.9;
        }

        .download-speed, .download-time {
            white-space: nowrap;
        }

        /* Responsive breakpoints para descargas activas */
        @media (max-width: 768px) {
            .descarga-item {
                padding: 1rem;
            }
            
            .descarga-item .text-truncate {
                max-width: 200px;
            }
            
            .descarga-item .btn-sm {
                min-width: 32px;
                height: 28px;
                padding: 0.2rem 0.4rem;
                font-size: 0.8rem;
            }
            
            .descarga-item .d-flex.justify-content-between {
                flex-direction: column;
                align-items: stretch;
            }
            
            .descarga-item .btn-group-responsive {
                margin-top: 0.5rem;
                justify-content: flex-start;
            }
        }

        @media (max-width: 576px) {
            .descarga-item .text-truncate {
                max-width: 150px;
            }
            
            .descarga-item .small.text-muted {
                font-size: 0.7rem;
            }
        }

        /* Video container mejorado */
        #video-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: var(--border-radius);
            padding: 1rem;
            margin-top: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        #video-container video {
            width: 100% !important;
            max-width: 800px !important;
            height: auto !important;
            aspect-ratio: 16/9 !important;
            object-fit: contain !important;
            background-color: #000 !important;
            border-radius: var(--border-radius-sm) !important;
            box-shadow: var(--box-shadow);
        }

        /* Indicadores de estado mejorados */
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 0.75rem;
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .status-downloading { background-color: var(--primary-color); }
        .status-done { background-color: var(--success-color); animation: none; }
        .status-error { background-color: var(--error-color); animation: none; }
        .status-cancelled { background-color: var(--warning-color); animation: none; }

        /* Estadísticas mejoradas */
        .download-stats {
            font-size: 0.875rem;
            color: #cbd5e0;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: var(--border-radius-sm);
            border-left: 3px solid var(--info-color);
        }

        /* Progress bar moderna */
        .progress {
            height: 8px !important;
            background: rgba(255, 255, 255, 0.2) !important;
            border-radius: 4px !important;
            overflow: hidden;
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.1);
        }

        .progress-bar {
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%) !important;
            transition: width 0.3s ease !important;
            position: relative;
        }

        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        /* URLs mejoradas */
        .url-metadata {
            color: #a7f3d0 !important;
            background: rgba(16, 185, 129, 0.1) !important;
            padding: 0.5rem 0.75rem !important;
            border-radius: var(--border-radius-sm) !important;
            display: inline-block !important;
            margin-top: 0.5rem !important;
            border: 1px solid rgba(16, 185, 129, 0.2) !important;
            font-family: 'Courier New', monospace !important;
        }

        .url-display {
            color: #e2e8f0 !important;
            background: rgba(15, 23, 42, 0.3) !important;
            padding: 0.75rem 1rem !important;
            border-radius: var(--border-radius-sm) !important;
            border-left: 4px solid var(--info-color) !important;
            margin: 0.75rem 0 !important;
            word-break: break-all;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
        }

        /* Texto responsive */
        .text-break {
            word-break: break-all;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
            line-height: 1.4;
        }

        /* Footer mejorado */
        .credit { 
            margin-top: 3rem; 
            font-size: 0.9rem; 
            color: rgba(255, 255, 255, 0.7); 
            text-align: center;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: var(--border-radius);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .credit a {
            color: #fbbf24;
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition);
        }

        .credit a:hover {
            color: #f59e0b;
            text-decoration: underline;
        }

        /* Botones pequeños mejorados */
        .btn-sm {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.875rem !important;
            border-radius: var(--border-radius-sm) !important;
            min-width: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .main {
                padding: 1.5rem;
                margin-left: 0;
                border-radius: 0;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .form-container {
                padding: 1.5rem;
            }
            
            .sidebar {
                padding: 1rem;
            }
            
            #video-container video {
                max-width: 100% !important;
            }
        }

        /* Loading states */
        .loading {
            position: relative;
            overflow: hidden;
        }

        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            animation: loading 1.5s infinite;
        }

        @keyframes loading {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        /* Tooltip styles */
        [title]:hover {
            position: relative;
        }

        /* Focus states para accesibilidad */
        .btn:focus,
        .form-control:focus {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }

        /* Animaciones suaves */
        * {
            transition: var(--transition);
        }

        /* Dashboard y estadísticas */
        .dashboard-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: var(--transition);
        }

        .dashboard-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--box-shadow-lg);
        }

        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: #fff;
            line-height: 1;
        }

        .stat-label {
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        .chart-container {
            height: 200px;
            position: relative;
            overflow: hidden;
        }

        /* Sistema de búsqueda y filtros */
        .search-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .search-input {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 2px solid transparent !important;
            border-radius: var(--border-radius-sm) !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            transition: var(--transition) !important;
            color: var(--dark-color) !important;
        }

        .search-input:focus {
            background: rgba(255, 255, 255, 1) !important;
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }

        .filter-chip {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            display: inline-block;
            margin: 0.25rem;
        }

        .filter-chip:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }

        .filter-chip.active {
            background: var(--primary-color);
            border-color: var(--primary-color);
        }

        /* Configuraciones */
        .config-section {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 1rem;
        }

        .config-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #fff;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .toggle-switch {
            position: relative;
            width: 50px;
            height: 25px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 25px;
            cursor: pointer;
            transition: var(--transition);
        }

        .toggle-switch.active {
            background: var(--success-color);
        }

        .toggle-switch::after {
            content: '';
            position: absolute;
            top: 2px;
            left: 2px;
            width: 21px;
            height: 21px;
            background: #fff;
            border-radius: 50%;
            transition: var(--transition);
        }

        .toggle-switch.active::after {
            transform: translateX(25px);
        }

        /* Organización por carpetas */
        .folder-tree {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .folder-item {
            display: flex;
            align-items: center;
            padding: 0.5rem;
            border-radius: var(--border-radius-sm);
            transition: var(--transition);
            cursor: pointer;
        }

        .folder-item:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .folder-icon {
            margin-right: 0.75rem;
            font-size: 1.2rem;
        }

        /* Cola de descargas */
        .queue-container {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .queue-item {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: var(--border-radius-sm);
            padding: 1rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: between;
            transition: var(--transition);
        }

        .queue-item:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .queue-number {
            background: var(--primary-color);
            color: #fff;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.875rem;
            margin-right: 1rem;
        }

        /* Tabs navigation */
        .nav-tabs-custom {
            border: none;
            margin-bottom: 2rem;
        }

        .nav-tabs-custom .nav-link {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: rgba(255, 255, 255, 0.7);
            margin-right: 0.5rem;
            border-radius: var(--border-radius-sm);
            padding: 0.75rem 1.5rem;
            transition: var(--transition);
        }

        .nav-tabs-custom .nav-link:hover {
            background: rgba(255, 255, 255, 0.15);
            color: #fff;
        }

        .nav-tabs-custom .nav-link.active {
            background: var(--primary-color);
            border-color: var(--primary-color);
            color: #fff;
        }

        /* Responsive improvements */
        @media (max-width: 768px) {
            .dashboard-card {
                padding: 1rem;
            }
            
            .stat-number {
                font-size: 2rem;
            }
            
            .search-container {
                padding: 1rem;
            }
            
            .filter-chip {
                margin: 0.25rem 0.125rem;
                padding: 0.4rem 0.8rem;
                font-size: 0.8rem;
            }
        }

        /* ================= Historial (layout responsive nombres largos) ================= */
        #historial-container {max-width:100%;}
        #historial-list {list-style:none;padding:0;margin:0;}
        .historial-item {display:grid;grid-template-columns:1fr auto;gap:.85rem;align-items:start;padding:.75rem 1rem;margin-bottom:.75rem;border-radius:14px;background:linear-gradient(145deg,rgba(255,255,255,.08),rgba(255,255,255,.02));border:1px solid rgba(255,255,255,.08);position:relative;}
        .historial-item:hover {background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.03));}
        .historial-main {min-width:0;}
        .historial-title {display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;word-break:break-word;font-weight:600;font-size:.8rem;line-height:1.15rem;text-decoration:none;color:#fff;}
        .historial-item.expanded .historial-title {-webkit-line-clamp:unset;}
        .historial-meta {font-size:.68rem;opacity:.78;margin-top:.35rem;word-break:break-word;}
        .historial-meta .url-metadata {display:block;margin-top:.25rem;}
        .historial-actions {display:flex;flex-direction:column;gap:.4rem;align-items:flex-end;min-width:70px;}
        .historial-actions .btn {white-space:nowrap;padding:4px 8px;font-size:.6rem;}
        .historial-actions .toggle-expand {background:#495065;border-color:#495065;color:#fff;}
        .historial-actions .toggle-expand.active {background:#2f7c4d;border-color:#2f7c4d;}
        @media (max-width:600px){
            .historial-item {grid-template-columns:1fr;}
            .historial-actions {flex-direction:row;flex-wrap:wrap;justify-content:flex-start;}
            .historial-actions .btn {flex:1 1 calc(50% - 6px);}
        }

        /* Scrollbar personalizada */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }
    </style>
</head>
<body>
<div class="container-fluid">
  <div class="row">
    <nav class="col-md-3 sidebar">
      <!-- Navegación por pestañas -->
      <ul class="nav nav-tabs nav-tabs-custom mb-3" id="sidebarTabs" role="tablist">
        <li class="nav-item" role="presentation">
          <button class="nav-link active" id="historial-tab" data-bs-toggle="tab" data-bs-target="#historial-pane" type="button" role="tab">
            📚 Historial
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="activas-tab" data-bs-toggle="tab" data-bs-target="#activas-pane" type="button" role="tab">
            ⬇️ Activas
          </button>
        </li>
        <li class="nav-item" role="presentation">
          <button class="nav-link" id="dashboard-tab" data-bs-toggle="tab" data-bs-target="#dashboard-pane" type="button" role="tab">
            📊 Stats
          </button>
        </li>
      </ul>

      <div class="tab-content" id="sidebarTabContent">
        <!-- Pestaña de Historial -->
        <div class="tab-pane fade show active" id="historial-pane" role="tabpanel">
          <h3>Historial de descargas</h3>
          
          <!-- Sistema de búsqueda y filtros -->
          <div class="search-container">
            <div class="mb-3">
              <input type="text" id="search-input" class="form-control search-input" placeholder="🔍 Buscar videos...">
            </div>
            <div class="mb-2">
              <small class="text-light opacity-75">Filtrar por:</small>
            </div>
            <div>
              <span class="filter-chip active" data-filter="all">Todos</span>
              <span class="filter-chip" data-filter="today">Hoy</span>
              <span class="filter-chip" data-filter="week">Esta semana</span>
              <span class="filter-chip" data-filter="large">Archivos grandes</span>
            </div>
          </div>

          {% if stats and stats.total > 0 %}
            <div class="download-stats">
              <small>
                📊 Activas: <span class="status-downloading">●</span> {{stats.downloading}} | 
                ✅ {{stats.completed}} | ❌ {{stats.errors}} | 🚫 {{stats.cancelled}}
              </small>
            </div>
            <hr style="margin: 0.5rem 0;">
          {% endif %}
          
          <div id="historial-container">
            {% if historial and historial|length > 0 %}
              <ul id="historial-list">
              {% for item in historial %}
                                <li class="historial-item" 
                                        data-filename="{{item.archivo|lower}}"
                                        data-date="{{item.fecha_timestamp or 0}}"
                                        data-size="{{item.tamaño_bytes or 0}}">
                                    <div class="historial-main">
                                        <a href="/static/{{item.archivo}}" download class="historial-title" title="{{item.archivo}}">{{item.archivo}}</a>
                                        <div class="historial-meta">
                                            📦 {{item.tamaño}} • 📅 {{item.fecha}}
                                            {% if item.url %}
                                                <span class="url-metadata">🔗 <span class="text-break" style="font-size:0.72em;">{{item.url}}</span></span>
                                            {% endif %}
                                        </div>
                                    </div>
                                    <div class="historial-actions">
                                        {% if item.url %}
                                        <button class="btn btn-outline-info btn-sm" data-url="{{item.url|e}}" onclick="copiarUrlFromData(this)" title="Copiar URL">📋</button>
                                        <button class="btn btn-outline-success btn-sm" data-url="{{item.url|e}}" onclick="reproducirUrlFromData(this)" title="Reproducir">▶️</button>
                                        {% endif %}
                                        <button class="btn btn-outline-warning btn-sm" data-filename="{{item.archivo|e}}" onclick="renombrarArchivoFromData(this)" title="Renombrar">✏️</button>
                                        <button class="btn btn-outline-danger btn-sm" data-filename="{{item.archivo|e}}" onclick="eliminarArchivoFromData(this)" title="Eliminar">🗑️</button>
                                        <button class="btn btn-sm toggle-expand" onclick="toggleHistItem(this)" title="Expandir/contraer">↕</button>
                                    </div>
                                </li>
              {% endfor %}
              </ul>
            {% else %}
              <span style="color:#ccc">No hay descargas aún.</span>
            {% endif %}
          </div>
        </div>

        <!-- Pestaña de Descargas Activas -->
        <div class="tab-pane fade" id="activas-pane" role="tabpanel">
          <h3>Descargas activas</h3>
          
          <!-- Cola de descargas -->
          <div class="queue-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <h5 class="mb-0">Cola de descargas</h5>
              <button class="btn btn-outline-light btn-sm" onclick="toggleQueue()">
                <span id="queue-toggle-text">▶️ Iniciar</span>
              </button>
            </div>
            <div id="download-queue" class="mb-3">
              <!-- Las URLs en cola aparecerán aquí -->
            </div>
            <div class="d-flex gap-2">
              <input type="text" id="queue-url-input" class="form-control form-control-sm" placeholder="URL M3U8 para añadir a la cola">
              <button class="btn btn-primary btn-sm" onclick="addToQueue()">➕</button>
            </div>
          </div>
          
          <div id="descargas-activas"></div>
        </div>

        <!-- Pestaña de Dashboard -->
        <div class="tab-pane fade" id="dashboard-pane" role="tabpanel">
          <h3>Dashboard</h3>
          
          <!-- Estadísticas generales -->
          <div class="row">
            <div class="col-6">
              <div class="dashboard-card text-center">
                <div class="stat-number" id="total-downloads">{{historial|length or 0}}</div>
                <div class="stat-label">Videos descargados</div>
              </div>
            </div>
            <div class="col-6">
              <div class="dashboard-card text-center">
                <div class="stat-number" id="total-size">0 GB</div>
                <div class="stat-label">Tamaño total</div>
              </div>
            </div>
          </div>
          
          <div class="row">
            <div class="col-6">
              <div class="dashboard-card text-center">
                <div class="stat-number" id="avg-speed">0</div>
                <div class="stat-label">Velocidad promedio</div>
              </div>
            </div>
            <div class="col-6">
              <div class="dashboard-card text-center">
                <div class="stat-number" id="success-rate">100%</div>
                <div class="stat-label">Tasa de éxito</div>
              </div>
            </div>
          </div>

          <!-- Configuraciones -->
          <div class="config-section">
            <div class="config-title">
              ⚙️ Configuraciones
            </div>
            
            <div class="row">
              <div class="col-12">
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <span>Descargas automáticas</span>
                  <div class="toggle-switch" id="auto-download-toggle" onclick="toggleConfig('autoDownload')"></div>
                </div>
                
                <div class="d-flex justify-content-between align-items-center mb-3">
                  <span>Notificaciones</span>
                  <div class="toggle-switch active" id="notifications-toggle" onclick="toggleConfig('notifications')"></div>
                </div>
                
                <div class="mb-3">
                  <label class="form-label">Máximo descargas simultáneas:</label>
                  <input type="range" class="form-range" min="1" max="10" value="5" id="max-concurrent-range" onchange="updateMaxConcurrent(this.value)">
                  <small class="text-light opacity-75">Actual: <span id="max-concurrent-value">5</span></small>
                </div>
                
                <div class="mb-3">
                  <label class="form-label">Calidad preferida:</label>
                  <select class="form-control" id="quality-select" onchange="updateQuality(this.value)">
                    <option value="auto">Automática</option>
                    <option value="1080p">1080p</option>
                    <option value="720p">720p</option>
                    <option value="480p">480p</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
    <main class="col-md-9 main">
      <h1>Descargador M3U8 Profesional</h1>
      <div class="form-container">
        <form id="descargar-form" class="mb-0">
          <div class="mb-3">
            <label for="m3u8-url" class="form-label fw-semibold">URL del video M3U8</label>
            <input type="text" name="m3u8_url" id="m3u8-url" class="form-control" placeholder="https://ejemplo.com/video.m3u8" value="{{ url }}" required>
            <div class="form-text text-light opacity-75">Pega aquí la URL del archivo M3U8 que deseas descargar</div>
          </div>
          <div class="mb-4">
            <label for="output-name" class="form-label fw-semibold">Nombre del archivo (opcional)</label>
            <input type="text" name="output_name" id="output-name" class="form-control" placeholder="mi-video">
            <div class="form-text text-light opacity-75">Sin extensión .mp4 - se añadirá automáticamente</div>
          </div>
          <div class="d-flex gap-3 flex-wrap">
            <button type="button" class="btn btn-info d-flex align-items-center gap-2" onclick="playM3U8()">
              <span>▶️</span> Vista Previa
            </button>
            <button type="button" class="btn btn-secondary d-flex align-items-center gap-2" onclick="extractMetadata()">
              <span>🔍</span> Analizar M3U8
            </button>
            <button type="submit" class="btn btn-success d-flex align-items-center gap-2">
              <span>⬇️</span> Descargar MP4
            </button>
            <button type="button" class="btn btn-outline-light d-flex align-items-center gap-2" onclick="addToQueueFromForm()">
              <span>➕</span> Añadir a Cola
            </button>
          </div>
        </form>
      </div>
      
      <!-- Área de metadatos M3U8 -->
      <div id="metadata-container" class="form-container" style="display: none;">
        <h5 class="fw-semibold mb-3">📋 Información del Video M3U8</h5>
        <div id="metadata-content"></div>
      </div>
      
      <div id="video-container"></div>
      <div id="progreso" class="mt-4"></div>
      <div class="credit">
        <div class="d-flex flex-column align-items-center gap-2">
          <div class="fw-semibold">🎬 Descargador M3U8 Profesional</div>
          <div class="small">
            Desarrollado con 
            <a href="https://github.com/video-dev/hls.js/" target="_blank">hls.js</a> • 
            <a href="https://flask.palletsprojects.com/" target="_blank">Flask</a> • 
            <a href="https://getbootstrap.com/" target="_blank">Bootstrap</a> • 
            <a href="https://ffmpeg.org/" target="_blank">FFmpeg</a>
          </div>
          <div class="small opacity-75">Versión 2.0.0 - Sistema completo con búsqueda, cola y dashboard</div>
          <div class="fw-bold" style="color: #fbbf24; margin-top: 0.5rem;">
            👨‍💻 Creado por <span style="color: #fff;">Ingeniero Kevin Aráuz</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
// Variables globales para las nuevas funcionalidades
let downloadQueue = [];
let queueRunning = false;
let userConfig = {
    autoDownload: false,
    notifications: true,
    maxConcurrent: 5,
    quality: 'auto'
};

// Objeto para trackear descargas activas para el cálculo de velocidad promedio
window.activeDownloads = {};

// Cargar configuración del localStorage
function loadUserConfig() {
    const saved = localStorage.getItem('m3u8_downloader_config');
    if (saved) {
        userConfig = { ...userConfig, ...JSON.parse(saved) };
        updateConfigUI();
    }
}

// Guardar configuración en localStorage
function saveUserConfig() {
    localStorage.setItem('m3u8_downloader_config', JSON.stringify(userConfig));
}

// Actualizar interfaz de configuración
function updateConfigUI() {
    document.getElementById('auto-download-toggle').classList.toggle('active', userConfig.autoDownload);
    document.getElementById('notifications-toggle').classList.toggle('active', userConfig.notifications);
    document.getElementById('max-concurrent-range').value = userConfig.maxConcurrent;
    document.getElementById('max-concurrent-value').textContent = userConfig.maxConcurrent;
    document.getElementById('quality-select').value = userConfig.quality;
}

// Toggle configuración
function toggleConfig(setting) {
    userConfig[setting] = !userConfig[setting];
    saveUserConfig();
    updateConfigUI();
    showNotification(setting + ' ' + (userConfig[setting] ? 'activado' : 'desactivado'), 'info');
}

// Actualizar configuraciones
function updateMaxConcurrent(value) {
    userConfig.maxConcurrent = parseInt(value);
    document.getElementById('max-concurrent-value').textContent = value;
    saveUserConfig();
}

function updateQuality(value) {
    userConfig.quality = value;
    saveUserConfig();
    showNotification('Calidad establecida: ' + value, 'info');
}

// Sistema de notificaciones
function showNotification(message, type = 'info') {
    if (!userConfig.notifications) return;
    
    const notification = document.createElement('div');
    notification.className = 'alert alert-' + type + ' position-fixed';
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        ${message}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Sistema de búsqueda y filtros
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    const filterChips = document.querySelectorAll('.filter-chip');
    
    searchInput.addEventListener('input', filterHistorial);
    
    filterChips.forEach(chip => {
        chip.addEventListener('click', function() {
            filterChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            filterHistorial();
        });
    });
}

function filterHistorial() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const activeFilter = document.querySelector('.filter-chip.active').dataset.filter;
    const items = document.querySelectorAll('.historial-item');
    
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    items.forEach(item => {
        const filename = item.dataset.filename;
        const date = new Date(parseInt(item.dataset.date) * 1000);
        const size = parseInt(item.dataset.size);
        
        // Filtro de búsqueda
        const matchesSearch = filename.includes(searchTerm);
        
        // Filtro de fecha/tipo
        let matchesFilter = true;
        switch(activeFilter) {
            case 'today':
                matchesFilter = date >= today;
                break;
            case 'week':
                matchesFilter = date >= weekAgo;
                break;
            case 'large':
                matchesFilter = size > 100 * 1024 * 1024; // > 100MB
                break;
        }
        
        item.style.display = (matchesSearch && matchesFilter) ? 'flex' : 'none';
    });
}

// Función para limpiar notificaciones de una descarga específica
function limpiarNotificacionesDescarga(download_id) {
    const tiposNotificacion = ['_cancelled', '_completed', '_error', '_paused'];
    tiposNotificacion.forEach(tipo => {
        notificacionesMostradas.delete(download_id + tipo);
    });
}

// Función para reanudar descarga
function reanudarDescarga(download_id) {
    // Limpiar notificaciones previas al reanudar
    limpiarNotificacionesDescarga(download_id);
    
    if (confirm('¿Reanudar esta descarga desde donde se quedó?')) {
        fetch('/reanudar/' + download_id, {
            method: 'POST'
        }).then(r => r.json()).then(data => {
            if (data.success) {
                // Agregar al tracking de descargas activas
                window.activeDownloads[download_id] = true;
                
                showNotification('Descarga reanudada', 'success');
                // Actualizar la interfaz
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification('Error al reanudar: ' + data.error, 'danger');
            }
        }).catch(error => {
            showNotification('Error al reanudar: ' + error.message, 'danger');
        });
    }
}

// Función para pausar descarga
function pausarDescarga(download_id) {
    if (confirm('¿Pausar esta descarga? Podrás reanudarla más tarde.')) {
        fetch('/pausar/' + download_id, {
            method: 'POST'
        }).then(r => r.json()).then(data => {
            if (data.success) {
                showNotification('Descarga pausada', 'info');
                // Actualizar la interfaz para mostrar estado pausado
                const pauseBtn = document.getElementById('pause-btn-' + download_id);
                const cancelBtn = document.getElementById('cancel-btn-' + download_id);
                if (pauseBtn) pauseBtn.style.display = 'none';
                if (cancelBtn) cancelBtn.style.display = 'none';
                
                // Actualizar el progreso para reflejar el estado pausado
                setTimeout(() => actualizarProgreso(download_id), 500);
            } else {
                showNotification('Error al pausar: ' + data.error, 'danger');
            }
        }).catch(error => {
            showNotification('Error al pausar: ' + error.message, 'danger');
        });
    }
}

// Función para renombrar archivo
function renombrarArchivo(filename) {
    const nombreActual = filename.replace('.mp4', '');
    const nuevoNombre = prompt('Nuevo nombre para el archivo (sin extensión):', nombreActual);

    if (nuevoNombre === null) {
        return;
    }
    
    const nuevoNombreLimpio = nuevoNombre.trim();
    
    if (!nuevoNombreLimpio) {
        showNotification('❌ El nuevo nombre no puede estar vacío', 'danger');
        return;
    }
    
    if (nuevoNombreLimpio === nombreActual) {
        return;
    }
    
    // Mostrar indicador de carga
    showNotification('🔄 Renombrando archivo...', 'info');
    
    fetch('/renombrar/' + encodeURIComponent(filename), {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({ nuevo_nombre: nuevoNombreLimpio })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification(`✅ Archivo renombrado a: ${data.nuevo_nombre}`, 'success');
            
            // Actualizar el historial cuando se renombre un archivo
            setTimeout(function() {
                updateHistorial();
            }, 500);
        } else {
            const errorMsg = data.error || 'Error desconocido';
            showNotification(`❌ Error al renombrar: ${errorMsg}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error en renombrado:', error);
        showNotification(`❌ Error de conexión: ${error.message}`, 'danger');
    });
}

// Función para renombrar archivo usando data-filename (versión segura)
function renombrarArchivoFromData(button) {
    const filename = button.getAttribute('data-filename');
    if (filename) {
        renombrarArchivo(filename);
    } else {
        console.error('❌ No se encontró data-filename en el botón');
        showNotification('❌ Error: No se pudo obtener el nombre del archivo', 'danger');
    }
}

// Función para eliminar archivo usando data-filename (versión segura)
function eliminarArchivoFromData(button) {
    const filename = button.getAttribute('data-filename');
    if (filename) {
        eliminarArchivo(filename);
    } else {
        console.error('❌ No se encontró data-filename en el botón');
        showNotification('❌ Error: No se pudo obtener el nombre del archivo', 'danger');
    }
}

// Función para renombrar descarga activa mientras se está descargando
function renombrarDescargaActiva(download_id) {
    // Obtener el nombre actual del archivo
    const archivoElement = document.getElementById('archivo-' + download_id);
    if (!archivoElement) {
        showNotification('❌ Error: No se pudo obtener la información de la descarga', 'danger');
        return;
    }
    
    const nombreActual = archivoElement.textContent || 'Archivo sin nombre';
    const nombreSinExtension = nombreActual.replace('.mp4', '').replace('Descargando: ', '').replace('Preparando descarga...', 'nuevo_archivo');
    
    const nuevoNombre = prompt('Nuevo nombre para el archivo (sin extensión):', nombreSinExtension);
    
    if (nuevoNombre === null) {
        return;
    }
    
    const nuevoNombreLimpio = nuevoNombre.trim();
    
    if (!nuevoNombreLimpio) {
        showNotification('❌ El nuevo nombre no puede estar vacío', 'danger');
        return;
    }
    
    if (nuevoNombreLimpio === nombreSinExtension) {
        return;
    }
    
    console.log('📤 Enviando solicitud de renombrado para descarga activa:', {
        download_id: download_id,
        nuevo_nombre: nuevoNombreLimpio
    });
    
    // Mostrar indicador de carga
    showNotification('🔄 Renombrando descarga activa...', 'info');
    
    fetch('/renombrar_descarga_activa/' + encodeURIComponent(download_id), {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({ nuevo_nombre: nuevoNombreLimpio })
    })
    .then(response => {
        console.log('📥 Respuesta recibida:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    })
    .then(data => {
        console.log('📄 Datos de respuesta:', data);
        
        if (data.success) {
            showNotification(`✅ Descarga renombrada a: ${data.nuevo_nombre}`, 'success');
            console.log('✅ Renombrado exitoso:', data.message);
            
            // Actualizar el nombre mostrado en la interfaz
            const archivoElement = document.getElementById('archivo-' + download_id);
            if (archivoElement) {
                const textoActual = archivoElement.textContent;
                let nuevoTexto = '';
                if (textoActual.includes('Descargando: ')) {
                    nuevoTexto = 'Descargando: ' + data.nuevo_nombre + '.mp4';
                } else if (textoActual.includes('Preparando descarga...')) {
                    nuevoTexto = 'Preparando: ' + data.nuevo_nombre + '.mp4';
                } else {
                    nuevoTexto = data.nuevo_nombre + '.mp4';
                }
                archivoElement.textContent = nuevoTexto;
                archivoElement.title = nuevoTexto; // Tooltip para ver el nombre completo
            }
        } else {
            const errorMsg = data.error || 'Error desconocido';
            console.error('❌ Error del servidor:', errorMsg);
            showNotification(`❌ Error al renombrar: ${errorMsg}`, 'danger');
        }
    })
    .catch(error => {
        console.error('❌ Error de red o JavaScript:', error);
        showNotification(`❌ Error de conexión: ${error.message}`, 'danger');
    });
}

// Mejorar la función de cola
function addToQueue() {
    const url = document.getElementById('queue-url-input').value.trim();
    const quality = userConfig.quality || 'best';
    
    if (!url) {
        showNotification('Introduce una URL válida', 'warning');
        return;
    }
    
    fetch('/api/queue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            action: 'add',
            url: url,
            name: '',
            quality: quality
        })
    }).then(r => r.json()).then(data => {
        if (data.success) {
            document.getElementById('queue-url-input').value = '';
            updateQueueDisplay();
            showNotification('URL añadida a la cola', 'success');
        } else {
            showNotification('Error: ' + data.error, 'danger');
        }
    }).catch(error => {
        showNotification('Error: ' + error.message, 'danger');
    });
}

function addToQueueFromForm() {
    const url = document.getElementById('m3u8-url').value.trim();
    const name = document.getElementById('output-name').value.trim();
    const quality = userConfig.quality || 'best';
    
    if (!url) {
        showNotification('Introduce una URL en el formulario principal', 'warning');
        return;
    }
    
    fetch('/api/queue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            action: 'add',
            url: url,
            name: name,
            quality: quality
        })
    }).then(r => r.json()).then(data => {
        if (data.success) {
            updateQueueDisplay();
            showNotification('URL añadida a la cola desde el formulario', 'success');
        } else {
            showNotification('Error: ' + data.error, 'danger');
        }
    }).catch(error => {
        showNotification('Error: ' + error.message, 'danger');
    });
}

function removeFromQueue(id) {
    fetch('/api/queue', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
    }).then(r => r.json()).then(data => {
        if (data.success) {
            updateQueueDisplay();
            showNotification('Elemento eliminado de la cola', 'info');
        } else {
            showNotification('Error: ' + data.error, 'danger');
        }
    }).catch(error => {
        showNotification('Error: ' + error.message, 'danger');
    });
}

function updateQueueDisplay() {
    fetch('/api/queue')
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const container = document.getElementById('download-queue');
                const toggleBtn = document.getElementById('queue-toggle-text');
                
                if (data.queue.length === 0) {
                    container.innerHTML = '<p class="text-center text-muted">La cola está vacía</p>';
                } else {
                    container.innerHTML = data.queue.map((item, index) => `
                        <div class="queue-item">
                            <div class="queue-number">${index + 1}</div>
                            <div class="flex-grow-1 me-2">
                                <div class="text-truncate">${item.name || 'Sin nombre'}</div>
                                <small class="text-muted text-break">${item.url}</small>
                                <div class="small text-info">Calidad: ${item.quality || 'best'}</div>
                            </div>
                            <div class="d-flex gap-1">
                                <button class="btn btn-outline-danger btn-sm" onclick="removeFromQueue('${item.id}')" title="Eliminar de la cola">
                                    🗑️
                                </button>
                            </div>
                        </div>
                    `).join('');
                }
                
                // Actualizar botón de toggle
                if (toggleBtn) {
                    toggleBtn.textContent = data.running ? 'Pausar' : 'Iniciar';
                }
                queueRunning = data.running;
            }
        })
        .catch(error => {
            console.error('Error actualizando cola:', error);
        });
}

function toggleQueue() {
    const action = queueRunning ? 'stop' : 'start';
    const toggleBtn = document.getElementById('queue-toggle-text');
    
    // Mostrar indicador de carga
    if (toggleBtn) {
        toggleBtn.textContent = action === 'start' ? '⏳ Iniciando...' : '⏳ Deteniendo...';
    }
    
    fetch('/api/queue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
    }).then(r => r.json()).then(data => {
        if (data.success) {
            queueRunning = !queueRunning;
            updateQueueDisplay();
            
            // Mensaje específico dependiendo de la acción
            if (queueRunning) {
                showNotification('Cola iniciada - Las descargas comenzarán automáticamente', 'success');
                // Forzar actualización inmediata de descargas activas
                setTimeout(loadActiveDownloads, 1000);
            } else {
                showNotification('Cola pausada', 'info');
            }
        } else {
            showNotification('Error: ' + data.error, 'danger');
            // Restaurar texto del botón en caso de error
            if (toggleBtn) {
                toggleBtn.textContent = queueRunning ? 'Pausar' : 'Iniciar';
            }
        }
    }).catch(error => {
        showNotification('Error: ' + error.message, 'danger');
        // Restaurar texto del botón en caso de error
        if (toggleBtn) {
            toggleBtn.textContent = queueRunning ? 'Pausar' : 'Iniciar';
        }
    });
}

// Actualizar estadísticas del dashboard
function updateDashboardStats() {
    // Calcular estadísticas
    const items = document.querySelectorAll('.historial-item');
    let totalSize = 0;
    let totalCount = items.length;
    
    items.forEach(item => {
        totalSize += parseInt(item.dataset.size || 0);
    });
    
    // Calcular velocidad promedio de descargas activas
    let avgSpeed = 0;
    let activeDownloads = 0;
    
    // Obtener velocidades de todas las descargas activas
    Object.keys(window.activeDownloads || {}).forEach(downloadId => {
        fetch('/progreso/' + downloadId)
            .then(r => r.json())
            .then(data => {
                if (data.status === 'downloading' && data.download_speed > 0) {
                    avgSpeed += data.download_speed;
                    activeDownloads++;
                    
                    // Actualizar solo si es la última descarga procesada
                    if (activeDownloads > 0) {
                        const finalAvgSpeed = (avgSpeed / activeDownloads).toFixed(2);
                        document.getElementById('avg-speed').textContent = finalAvgSpeed + ' MB/s';
                    }
                }
            })
            .catch(() => {
                // Ignorar errores
            });
    });
    
    // Si no hay descargas activas, mostrar 0
    if (Object.keys(window.activeDownloads || {}).length === 0) {
        document.getElementById('avg-speed').textContent = '0 MB/s';
    }
    
    // Actualizar interfaz
    document.getElementById('total-downloads').textContent = totalCount;
    document.getElementById('total-size').textContent = formatFileSize(totalSize);
    
    // Calcular tasa de éxito (simplificado)
    const activeStats = JSON.parse(localStorage.getItem('download_stats') || '{"success": 0, "total": 0}');
    const successRate = activeStats.total > 0 ? Math.round((activeStats.success / activeStats.total) * 100) : 100;
    document.getElementById('success-rate').textContent = successRate + '%';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Manejador global de errores para filtrar errores de extensiones de Chrome
window.addEventListener('error', function(event) {
    // Filtrar errores conocidos de extensiones de Chrome
    const extensionErrors = [
        'runtime.lastError',
        'Extension context invalidated',
        'message channel closed',
        'ResizeObserver loop limit exceeded'
    ];
    
    const isExtensionError = extensionErrors.some(errorText => 
        event.message && event.message.includes(errorText)
    );
    
    if (isExtensionError) {
        // No mostrar estos errores al usuario, solo log silencioso
        console.debug('Extension error filtered:', event.message);
        event.preventDefault();
        return true;
    }
    
    // Para errores reales de nuestra aplicación, mantener el comportamiento normal
    return false;
});

// Suprimir advertencias específicas de runtime.lastError en la consola
const originalConsoleError = console.error;
console.error = function(...args) {
    const message = args.join(' ');
    if (message.includes('runtime.lastError') || 
        message.includes('message channel closed') ||
        message.includes('Extension context invalidated')) {
        // Silenciar estos errores específicos
        return;
    }
    originalConsoleError.apply(console, args);
};

// Función para limpiar duplicados de descargas
function cleanupDuplicateDownloads() {
    const activasContainer = document.getElementById('descargas-activas');
    const seenIds = new Set();
    const elementsToRemove = [];
    
    activasContainer.querySelectorAll('[data-download-id]').forEach(el => {
        const downloadId = el.dataset.downloadId;
        if (seenIds.has(downloadId)) {
            // Es un duplicado, marcarlo para eliminación
            elementsToRemove.push(el);
            console.log('Encontrado duplicado, marcando para eliminación:', downloadId);
        } else {
            seenIds.add(downloadId);
        }
    });
    
    // Eliminar duplicados
    elementsToRemove.forEach(el => {
        console.log('Eliminando elemento duplicado:', el.dataset.downloadId);
        el.remove();
    });
    
    if (elementsToRemove.length > 0) {
        console.log(`Limpiados ${elementsToRemove.length} duplicados`);
    }
}

// Inicialización al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    loadUserConfig();
    initializeSearch();
    updateQueueDisplay();
    updateDashboardStats();
    
    // Cargar descargas activas persistentes
    loadActiveDownloads();
    
    // Limpiar duplicados cada 10 segundos
    setInterval(cleanupDuplicateDownloads, 10000);
    
    // Actualizar progreso cada 2 segundos
    setInterval(actualizarTodasLasDescargas, 2000);
    
    // Actualizar estadísticas cada 30 segundos
    setInterval(updateDashboardStats, 30000);
    
    // Actualizar cola cada 5 segundos (más frecuente)
    setInterval(updateQueueDisplay, 5000);
    
    // Actualizar descargas activas cada 5 segundos
    setInterval(loadActiveDownloads, 5000);
    
    // Cargar el historial inicial
    updateHistorial();
    
    // Actualizar historial cada 30 segundos
    setInterval(updateHistorial, 30000);
});

// Función para cargar descargas activas al refrescar
function loadActiveDownloads() {
    // Cargar todas las descargas que no están completadas
    fetch('/api/active_downloads')
        .then(r => r.json())
        .then(data => {
            if (data.success && data.downloads) {
                const activasContainer = document.getElementById('descargas-activas');
                
                // Obtener IDs ya mostrados para evitar duplicados
                const existingIds = new Set();
                const existingElements = new Map(); // Para mapear ID -> elemento
                
                activasContainer.querySelectorAll('[data-download-id]').forEach(el => {
                    const downloadId = el.dataset.downloadId;
                    existingIds.add(downloadId);
                    existingElements.set(downloadId, el);
                });
                
                // Procesar descargas del servidor
                const serverDownloadIds = new Set();
                Object.keys(data.downloads).forEach(download_id => {
                    const download = data.downloads[download_id];
                    serverDownloadIds.add(download_id);
                    
                    if (['downloading', 'paused', 'error', 'cancelled'].includes(download.status)) {
                        if (!existingIds.has(download_id)) {
                            // Solo crear nuevo elemento si NO existe
                            console.log('Creando nueva descarga activa:', download_id);
                            mostrarDescargaActiva(download_id, download.url);
                        } else {
                            // Ya existe, solo actualizar si es necesario
                            console.log('Descarga ya existe, saltando:', download_id);
                        }
                    }
                });
                
                // Remover descargas que ya no están en el servidor o están completas
                existingElements.forEach((element, downloadId) => {
                    if (!serverDownloadIds.has(downloadId) || 
                        (data.downloads[downloadId] && data.downloads[downloadId].status === 'done')) {
                        console.log('Removiendo descarga finalizada:', downloadId);
                        element.remove();
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error cargando descargas activas:', error);
        });
}

// Función para actualizar el historial dinámicamente
function updateHistorial() {
    fetch('/api/historial')
        .then(r => r.json())
        .then(data => {
            if (data.success && data.historial) {
                const historialContainer = document.getElementById('historial-container');
                
                if (data.historial.length === 0) {
                    historialContainer.innerHTML = '<p class="text-center text-muted">No hay descargas en el historial</p>';
                } else {
                    let html = '<ul id="historial-list">';
                    
            data.historial.forEach((item) => {
            const safeName = item.archivo.replace(/"/g,'&quot;');
            html += '<li class="historial-item" ' +
                'data-filename="' + item.archivo.toLowerCase() + '" ' +
                'data-date="' + (item.fecha_timestamp || 0) + '" ' +
                'data-size="' + (item.tamaño_bytes || 0) + '">' +
                '<div class="historial-main">' +
                '<a href="/static/' + safeName + '" download class="historial-title" title="' + safeName + '">' + safeName + '</a>' +
                '<div class="historial-meta">' +
                item.tamaño + ' • ' + item.fecha;
            if(item.url){
                html += '<span class="url-metadata">🔗 <span class="text-break" style="font-size:0.72em;">' + item.url + '</span></span>';
            }
            html += '</div></div>' +
                '<div class="historial-actions">';
            if(item.url){
                html += '<button class="btn btn-outline-info btn-sm" data-url="' + item.url + '" onclick="copiarUrlFromData(this)" title="Copiar URL">📋</button>' +
                    '<button class="btn btn-outline-success btn-sm" data-url="' + item.url + '" onclick="reproducirUrlFromData(this)" title="Reproducir">▶️</button>';
            }
            html += '<button class="btn btn-outline-warning btn-sm" data-filename="' + safeName + '" onclick="renombrarArchivoFromData(this)" title="Renombrar">✏️</button>' +
                '<button class="btn btn-outline-danger btn-sm" data-filename="' + safeName + '" onclick="eliminarArchivoFromData(this)" title="Eliminar">🗑️</button>' +
                '<button class="btn btn-sm toggle-expand" onclick="toggleHistItem(this)" title="Expandir/contraer">↕</button>' +
                '</div></li>';
            });
                    
                    html += '</ul>';
                    historialContainer.innerHTML = html;
                }
                
                // Actualizar contador de descargas totales
                const totalElement = document.getElementById('total-downloads');
                if (totalElement) {
                    totalElement.textContent = data.historial.length;
                }
            } else {
                console.error('❌ Error en respuesta del historial:', data);
            }
        })
        .catch(error => {
            console.error('Error actualizando historial:', error);
        });
}

// Expandir / contraer un ítem de historial (mostrar nombre completo)
function toggleHistItem(btn){
    const item = btn.closest('.historial-item');
    if(!item) return;
    const expanded = item.classList.toggle('expanded');
    btn.classList.toggle('active', expanded);
    btn.textContent = expanded ? '⇡' : '↕';
}

// Función para extraer y mostrar metadatos M3U8
function extractMetadata() {
    const url = document.getElementById('m3u8-url').value.trim();
    if (!url) {
        showNotification('Introduce una URL M3U8 válida', 'warning');
        return;
    }
    
    // Mostrar indicador de carga
    const metadataContainer = document.getElementById('metadata-container');
    const metadataContent = document.getElementById('metadata-content');
    
    metadataContainer.style.display = 'block';
    metadataContent.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Analizando...</span>
            </div>
            <p class="mt-2">Analizando archivo M3U8...</p>
        </div>
    `;
    
    fetch('/api/metadata', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    })
    .then(r => {
        if (!r.ok) {
            throw new Error('HTTP ' + r.status + ': ' + r.statusText);
        }
        return r.json();
    })
    .then(data => {
        if (data.success) {
            displayMetadata(data.metadata, data.suggested_filename);
            
            // Mostrar advertencia si es un fallback
            if (data.warning) {
                showNotification(data.warning, 'warning');
            }
            
            // Auto-rellenar nombre si está vacío
            const nameInput = document.getElementById('output-name');
            if (!nameInput.value && data.suggested_filename) {
                nameInput.value = data.suggested_filename;
                if (!data.warning) {
                    showNotification('Nombre sugerido aplicado automáticamente', 'info');
                } else {
                    showNotification('Nombre básico aplicado (metadatos no disponibles)', 'info');
                }
            }
        } else {
            metadataContent.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${data.error || 'Error desconocido'}
                </div>
            `;
            console.error('Error del servidor:', data.error);
        }
    })
    .catch(error => {
        console.error('Error completo:', error);
        metadataContent.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error de conexión:</strong> ${error.message}
                <br><small>Revisa la consola del navegador para más detalles</small>
            </div>
        `;
    });
}

function displayMetadata(metadata, suggestedName) {
    const metadataContent = document.getElementById('metadata-content');
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <div class="mb-3">
                    <label class="form-label fw-semibold">📝 Nombre Sugerido:</label>
                    <div class="input-group">
                        <input type="text" class="form-control" id="suggested-name" value="${suggestedName || 'No detectado'}" readonly>
                        <button class="btn btn-outline-primary" onclick="applySuggestedName()" title="Aplicar nombre sugerido">
                            ✅ Usar
                        </button>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="mb-3">
                    <label class="form-label fw-semibold">📐 Resolución:</label>
                    <input type="text" class="form-control" value="${metadata.resolution || 'No detectada'}" readonly>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-4">
                <div class="mb-3">
                    <label class="form-label fw-semibold">🎭 Calidad:</label>
                    <input type="text" class="form-control" value="${metadata.quality || 'Auto'}" readonly>
                </div>
            </div>
            <div class="col-md-4">
                <div class="mb-3">
                    <label class="form-label fw-semibold">📊 Bitrate:</label>
                    <input type="text" class="form-control" value="${metadata.bitrate || 'No detectado'}" readonly>
                </div>
            </div>
            <div class="col-md-4">
                <div class="mb-3">
                    <label class="form-label fw-semibold">⏱️ Duración Seg.:</label>
                    <input type="text" class="form-control" value="${metadata.duration ? metadata.duration + 's' : 'No detectada'}" readonly>
                </div>
            </div>
        </div>`;
    
    if (metadata.title) {
        html += `
            <div class="mb-3">
                <label class="form-label fw-semibold">🎬 Título Detectado:</label>
                <input type="text" class="form-control" value="${metadata.title}" readonly>
            </div>`;
    }
    
    if (metadata.video_info) {
        const info = metadata.video_info;
        html += `
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">🌐 Dominio:</label>
                        <input type="text" class="form-control" value="${info.source_domain || 'Desconocido'}" readonly>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-3">
                        <label class="form-label fw-semibold">📦 Segmentos Estimados:</label>
                        <input type="text" class="form-control" value="${info.estimated_segments || 'No calculado'}" readonly>
                    </div>
                </div>
            </div>`;
        
        if (info.is_live) {
            html += `
                <div class="alert alert-warning">
                    <strong>⚠️ Transmisión en Vivo:</strong> Este parece ser un stream en vivo. La descarga podría no funcionar correctamente.
                </div>`;
        }
    }
    
    html += `
        <div class="d-flex gap-2 mt-3">
            <button class="btn btn-outline-secondary btn-sm" onclick="hideMetadata()">
                ❌ Ocultar
            </button>
            <button class="btn btn-primary btn-sm" onclick="downloadWithMetadata()">
                ⬇️ Descargar con esta Información
            </button>
        </div>
    `;
    
    metadataContent.innerHTML = html;
}

function applySuggestedName() {
    const suggestedName = document.getElementById('suggested-name').value;
    if (suggestedName && suggestedName !== 'No detectado') {
        document.getElementById('output-name').value = suggestedName;
        showNotification('Nombre aplicado al formulario', 'success');
    }
}

function hideMetadata() {
    document.getElementById('metadata-container').style.display = 'none';
}

function downloadWithMetadata() {
    // Aplicar nombre sugerido si no hay uno
    const nameInput = document.getElementById('output-name');
    const suggestedInput = document.getElementById('suggested-name');
    
    if (!nameInput.value && suggestedInput && suggestedInput.value !== 'No detectado') {
        nameInput.value = suggestedInput.value;
    }
    
    // Ocultar metadatos y iniciar descarga
    hideMetadata();
    
    // Simular envío del formulario
    document.getElementById('descargar-form').dispatchEvent(new Event('submit'));
}

function playM3U8() {
    const url = document.getElementById('m3u8-url').value.trim();
    const container = document.getElementById('video-container');
    container.innerHTML = '';
    if (!url) {
        container.innerHTML = '<p>Por favor ingresa una URL M3U8 válida.</p>';
        return;
    }
    
    const video = document.createElement('video');
    video.controls = true;
    video.autoplay = true;
    video.style.marginTop = '1rem';
    video.style.width = '600px';
    video.style.height = '400px';
    video.style.maxWidth = '100%';
    video.style.objectFit = 'contain';
    video.style.backgroundColor = '#000';
    container.appendChild(video);
    
    if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(url);
        hls.attachMedia(video);
        hls.on(Hls.Events.ERROR, function(event, data) {
            if (data.fatal) {
                container.innerHTML = '<p style="color:#ff8080">Error al cargar el video M3U8.</p>';
            }
        });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = url;
        video.addEventListener('error', function() {
            container.innerHTML = '<p style="color:#ff8080">Error al cargar el video M3U8.</p>';
        });
    } else {
        container.innerHTML = '<p>Tu navegador no soporta reproducción M3U8.</p>';
    }
}

document.getElementById('descargar-form').addEventListener('submit', function(e) {
    e.preventDefault();
    let url = document.getElementById('m3u8-url').value.trim();
    let outputName = document.getElementById('output-name').value.trim();
    let params = 'm3u8_url=' + encodeURIComponent(url);
    if (outputName) params += '&output_name=' + encodeURIComponent(outputName);
    fetch('/descargar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params
    }).then(r => r.json()).then(data => {
        if (data.download_id) {
            let url = document.getElementById('m3u8-url').value.trim();
            // Limpiar notificaciones previas antes de iniciar una nueva descarga
            limpiarNotificacionesDescarga(data.download_id);
            mostrarDescargaActiva(data.download_id, url);
            showNotification('Descarga iniciada', 'success');
        } else if (data.error) {
            showNotification(data.error, 'danger');
        }
    });
});

function mostrarDescargaActiva(download_id, url) {
    // Verificar si ya existe un elemento para esta descarga
    const existingElement = document.getElementById('descarga-' + download_id);
    if (existingElement) {
        console.log('Elemento de descarga ya existe, no creando duplicado:', download_id);
        return; // No crear duplicado
    }
    
    // Agregar a tracking de descargas activas para cálculo de velocidad
    window.activeDownloads[download_id] = true;
    
    let div = document.getElementById('descargas-activas');
    let barra = document.createElement('div');
    barra.id = 'descarga-' + download_id;
    barra.className = 'descarga-item';
    barra.setAttribute('data-download-id', download_id);
    
    // Crear estructura responsiva usando flexbox
    // Contenedor principal con flexbox
    const mainContainer = document.createElement('div');
    mainContainer.className = 'd-flex flex-column';
    
    // Fila superior: título y botones (siempre visibles)
    const topRow = document.createElement('div');
    topRow.className = 'd-flex justify-content-between align-items-start flex-wrap mb-2';
    
    // Contenedor del título (lado izquierdo)
    const titleContainer = document.createElement('div');
    titleContainer.className = 'flex-grow-1 me-3';
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'd-flex align-items-center mb-1';
    const statusSpan = document.createElement('span');
    statusSpan.className = 'status-indicator status-downloading me-2';
    const titleStrong = document.createElement('strong');
    titleStrong.id = 'archivo-' + download_id;
    titleStrong.className = 'text-truncate';
    titleStrong.style.maxWidth = '300px';
    titleStrong.textContent = 'Preparando descarga...';
    titleStrong.title = 'Preparando descarga...'; // Tooltip para ver el nombre completo
    titleDiv.appendChild(statusSpan);
    titleDiv.appendChild(titleStrong);
    
    // Stats en línea compacta
    const statsDiv = document.createElement('div');
    statsDiv.className = 'download-stats small';
    statsDiv.id = 'stats-' + download_id;
    statsDiv.textContent = 'Inicializando...';
    
    titleContainer.appendChild(titleDiv);
    titleContainer.appendChild(statsDiv);
    
    // Contenedor de botones (lado derecho) - siempre visible
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'd-flex flex-wrap gap-1 align-items-start';
    buttonContainer.style.minWidth = '220px'; // Ancho mínimo para botones
    
    // Botón reproducir
    const playBtn = document.createElement('button');
    playBtn.className = 'btn btn-success btn-sm';
    playBtn.id = 'play-btn-' + download_id;
    playBtn.innerHTML = '▶️';
    playBtn.title = 'Reproducir video mientras se descarga';
    playBtn.onclick = function() { reproducirUrlActiva(download_id); };
    
    // Botón pausar descarga
    const pauseBtn = document.createElement('button');
    pauseBtn.className = 'btn btn-warning btn-sm';
    pauseBtn.id = 'pause-btn-' + download_id;
    pauseBtn.innerHTML = '⏸️';
    pauseBtn.title = 'Pausar descarga';
    pauseBtn.onclick = function() { pausarDescarga(download_id); };
    
    // Botón cancelar
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-danger btn-sm';
    cancelBtn.id = 'cancel-btn-' + download_id;
    cancelBtn.textContent = '❌';
    cancelBtn.title = 'Cancelar descarga';
    cancelBtn.onclick = function() { cancelarDescarga(download_id); };
    
    // Botón renombrar
    const renameBtn = document.createElement('button');
    renameBtn.className = 'btn btn-outline-warning btn-sm';
    renameBtn.id = 'rename-btn-' + download_id;
    renameBtn.innerHTML = '✏️';
    renameBtn.title = 'Renombrar archivo mientras se descarga';
    renameBtn.onclick = function() { renombrarDescargaActiva(download_id); };
    
    buttonContainer.appendChild(playBtn);
    buttonContainer.appendChild(pauseBtn);
    buttonContainer.appendChild(cancelBtn);
    buttonContainer.appendChild(renameBtn);
    
    topRow.appendChild(titleContainer);
    topRow.appendChild(buttonContainer);
    
    // Fila de progreso
    const progressContainer = document.createElement('div');
    progressContainer.className = 'mb-2';
    
    const progressTextDiv = document.createElement('div');
    progressTextDiv.className = 'd-flex justify-content-between align-items-center small mb-1';
    progressTextDiv.innerHTML = '<span>Progreso: <span id="progreso-' + download_id + '">0%</span></span>';
    
    // Progress bar
    const progressDiv = document.createElement('div');
    progressDiv.className = 'progress';
    progressDiv.style.height = '8px';
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    progressBar.id = 'bar-' + download_id;
    progressBar.setAttribute('role', 'progressbar');
    progressBar.style.width = '0%';
    progressDiv.appendChild(progressBar);
    
    progressContainer.appendChild(progressTextDiv);
    progressContainer.appendChild(progressDiv);
    
    // Fila de información adicional (velocidad, tiempo)
    const infoRow = document.createElement('div');
    infoRow.className = 'd-flex flex-wrap gap-3 small text-muted mb-2';
    
    // Speed div - mostrar velocidad de descarga
    const speedDiv = document.createElement('div');
    speedDiv.className = 'download-speed';
    speedDiv.id = 'speed-' + download_id;
    speedDiv.innerHTML = '<strong>💨</strong> <span>Calculando...</span>';
    
    // Time div - mostrar tiempos de descarga
    const timeDiv = document.createElement('div');
    timeDiv.className = 'download-time';
    timeDiv.id = 'time-' + download_id;
    timeDiv.innerHTML = '<strong>⏱️</strong> <span>00:00</span>';
    
    infoRow.appendChild(speedDiv);
    infoRow.appendChild(timeDiv);
    
    // URL div (colapsible para ahorrar espacio)
    const urlContainer = document.createElement('div');
    urlContainer.className = 'mt-1';
    
    const urlToggle = document.createElement('button');
    urlToggle.className = 'btn btn-link btn-sm p-0 small text-info';
    urlToggle.innerHTML = '🔗 Mostrar URL';
    urlToggle.onclick = function() {
        const urlDiv = document.getElementById('url-' + download_id);
        if (urlDiv.style.display === 'none') {
            urlDiv.style.display = 'block';
            urlToggle.innerHTML = '🔗 Ocultar URL';
        } else {
            urlDiv.style.display = 'none';
            urlToggle.innerHTML = '🔗 Mostrar URL';
        }
    };
    
    const urlDiv = document.createElement('div');
    urlDiv.className = 'url-display small mt-1';
    urlDiv.id = 'url-' + download_id;
    urlDiv.style.display = 'none'; // Inicialmente oculto
    urlDiv.innerHTML = '<span class="text-break">' + (url || 'N/A') + '</span>';
    
    urlContainer.appendChild(urlToggle);
    urlContainer.appendChild(urlDiv);
    
    // Ensamblar todo
    mainContainer.appendChild(topRow);
    mainContainer.appendChild(progressContainer);
    mainContainer.appendChild(infoRow);
    mainContainer.appendChild(urlContainer);
    
    barra.appendChild(mainContainer);
    div.appendChild(barra);
    console.log('Creado nuevo elemento de descarga responsivo:', download_id);
    
    if (url) {
        let copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-outline-info btn-sm';
        copyBtn.innerHTML = '📋';
        copyBtn.title = 'Copiar URL';
        copyBtn.onclick = function() { copiarUrl(url); };
        urlDiv.appendChild(copyBtn);
    }
    
    actualizarProgreso(download_id);
}

// Función para actualizar el progreso de todas las descargas activas
function actualizarTodasLasDescargas() {
    // Buscar todos los elementos de descarga activos
    const descargaElements = document.querySelectorAll('[id^="descarga-"]');
    
    descargaElements.forEach(element => {
        const download_id = element.id.replace('descarga-', '');
        // Validar que el download_id es válido y el elemento realmente existe
        if (download_id && download_id !== 'undefined' && document.getElementById('descarga-' + download_id)) {
            actualizarProgreso(download_id);
        }
    });
}

// Variable global para rastrear notificaciones ya mostradas
const notificacionesMostradas = new Set();

function actualizarProgreso(download_id) {
    // Validar que download_id existe y no es undefined
    if (!download_id || download_id === 'undefined') {
        return;
    }
    
    // Verificar que el elemento de descarga aún existe antes de hacer fetch
    if (!document.getElementById('descarga-' + download_id)) {
        return;
    }
    
    fetch('/progreso/' + download_id)
        .then(r => {
            if (!r.ok) {
                throw new Error('HTTP ' + r.status);
            }
            return r.json();
        })
        .then(data => {
        // Verificar nuevamente que el elemento existe (puede haber sido eliminado durante el fetch)
        if (!document.getElementById('descarga-' + download_id)) {
            return;
        }
        
        let bar = document.getElementById('bar-' + download_id);
        let prog = document.getElementById('progreso-' + download_id);
        let archivo = document.getElementById('archivo-' + download_id);
        let cancelBtn = document.getElementById('cancel-btn-' + download_id);
        let descargaDiv = document.getElementById('descarga-' + download_id);
        let stats = document.getElementById('stats-' + download_id);
        let speedElement = document.getElementById('speed-' + download_id);
        let timeElement = document.getElementById('time-' + download_id);
        
        if (data.output_file && archivo) {
            const fullText = 'Descargando: ' + data.output_file;
            archivo.innerHTML = '<span class="status-indicator status-' + data.status + '"></span>' + fullText;
            archivo.title = fullText; // Tooltip para ver el nombre completo
        }
        
        if (stats && data.total > 0) {
            let segmentos = (data.current || 0) + '/' + data.total + ' segmentos';
            if (data.status === 'downloading') {
                let velocidadTexto = '';
                
                // Mostrar velocidad en MB/s si está disponible
                if (data.download_speed && data.download_speed > 0) {
                    velocidadTexto = data.download_speed.toFixed(2) + ' MB/s';
                } else {
                    // Fallback a segmentos por minuto
                    let velocidad = data.current && data.start_time ? 
                        ((data.current / (Date.now()/1000 - data.start_time)) * 60).toFixed(1) : '0';
                    velocidadTexto = velocidad + ' seg/min';
                }
                
                // Agregar información de tiempo
                let tiempoTexto = '';
                if (data.elapsed_time_formatted) {
                    tiempoTexto = ' • Transcurrido: ' + data.elapsed_time_formatted;
                }
                if (data.estimated_time_formatted && data.estimated_time > 0) {
                    tiempoTexto += ' • Resta: ' + data.estimated_time_formatted;
                }
                
                stats.innerText = segmentos + ' • ' + velocidadTexto + tiempoTexto;
            } else {
                stats.innerText = segmentos;
            }
        }
        
        // Actualizar elemento de velocidad separado
        if (speedElement && data.status === 'downloading') {
            if (data.download_speed && data.download_speed > 0) {
                const speedMBs = data.download_speed.toFixed(2);
                const speedKBs = (data.download_speed * 1024).toFixed(0);
                speedElement.innerHTML = `<strong>Velocidad:</strong> <span class="text-primary">${speedMBs} MB/s (${speedKBs} KB/s)</span>`;
            } else {
                speedElement.innerHTML = '<strong>Velocidad:</strong> <span class="text-muted">Calculando...</span>';
            }
        } else if (speedElement) {
            speedElement.innerHTML = '<strong>Velocidad:</strong> <span class="text-muted">-</span>';
        }
        
        // Actualizar elemento de tiempo separado
        if (timeElement && data.status === 'downloading') {
            let tiempoHtml = '<strong>Tiempo:</strong> ';
            
            if (data.elapsed_time_formatted) {
                tiempoHtml += `<span class="text-warning">${data.elapsed_time_formatted} transcurrido</span>`;
                
                if (data.estimated_time_formatted && data.estimated_time > 0) {
                    tiempoHtml += ` • <span class="text-info">${data.estimated_time_formatted} restante</span>`;
                }
            } else {
                tiempoHtml += '<span class="text-muted">Calculando...</span>';
            }
            
            timeElement.innerHTML = tiempoHtml;
        } else if (timeElement && data.status === 'done') {
            if (data.total_time_formatted) {
                timeElement.innerHTML = `<strong>Tiempo total:</strong> <span class="text-success">${data.total_time_formatted}</span>`;
            } else {
                timeElement.innerHTML = '<strong>Tiempo:</strong> <span class="text-success">Completado</span>';
            }
        } else if (timeElement) {
            timeElement.innerHTML = '<strong>Tiempo:</strong> <span class="text-muted">-</span>';
        }
        
        if (data.status === 'downloading') {
            if (bar) bar.style.width = data.porcentaje + '%';
            if (prog) prog.innerText = data.porcentaje + '%';
            if (descargaDiv) descargaDiv.className = 'descarga-item';
            
            // Asegurar que los botones correctos están visibles para descargas en progreso
            let playBtn = document.getElementById('play-btn-' + download_id);
            let pauseBtn = document.getElementById('pause-btn-' + download_id);
            let cancelBtn = document.getElementById('cancel-btn-' + download_id);
            
            if (playBtn) playBtn.style.display = 'inline-block';
            if (pauseBtn) pauseBtn.style.display = 'inline-block';
            if (cancelBtn) cancelBtn.style.display = 'inline-block';
            
            setTimeout(function() { actualizarProgreso(download_id); }, 1000);
        } else if (data.status === 'done') {
            // Remover del tracking de descargas activas
            delete window.activeDownloads[download_id];
            
            if (bar) bar.style.width = '100%';
            if (prog) prog.innerText = '100%';
            if (archivo) archivo.innerHTML = '<span class="status-indicator status-done"></span>Completado: ' + data.output_file;
            if (descargaDiv) descargaDiv.className += ' descarga-done';
            
            // Ocultar botones de descarga activa
            let playBtn = document.getElementById('play-btn-' + download_id);
            let pauseBtn = document.getElementById('pause-btn-' + download_id);
            let cancelBtn = document.getElementById('cancel-btn-' + download_id);
            
            if (playBtn) playBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'none';
            if (cancelBtn) cancelBtn.style.display = 'none';
            
            if (stats) {
                let tiempoTotal = '';
                if (data.total_time_formatted) {
                    tiempoTotal = 'Completado en ' + data.total_time_formatted;
                } else if (data.end_time && data.start_time) {
                    let duracion = Math.round(data.end_time - data.start_time);
                    tiempoTotal = 'Completado en ' + duracion + 's';
                } else {
                    tiempoTotal = 'Completado';
                }
                
                // Agregar velocidad promedio si está disponible
                if (data.download_speed && data.download_speed > 0) {
                    tiempoTotal += ' • Velocidad promedio: ' + data.download_speed.toFixed(2) + ' MB/s';
                }
                
                stats.innerText = tiempoTotal;
            }
            let descargaElement = document.getElementById('descarga-' + download_id);
            if (descargaElement) {
                descargaElement.innerHTML += 
                    '<div class="mt-2">' +
                        '<a href="/static/' + data.output_file + '" download class="btn btn-primary btn-sm me-2">Descargar MP4</a>' +
                        '<button class="btn btn-outline-secondary btn-sm" onclick="eliminarDescargaActiva(\\"' + download_id + '\\")" title="Eliminar de la lista">' +
                            'Quitar' +
                        '</button>' +
                    '</div>';
            }
            
            // Mostrar notificación solo una vez
            const notificationKey = download_id + '_completed';
            if (!notificacionesMostradas.has(notificationKey)) {
                notificacionesMostradas.add(notificationKey);
                showNotification('Descarga completada: ' + data.output_file, 'success');
            }
            
            // Actualizar el historial cuando se complete una descarga
            setTimeout(function() { 
                updateHistorial();
            }, 1000);
            
            setTimeout(function() { 
                location.reload(); 
            }, 3000);
        } else if (data.status === 'error') {
            // Remover del tracking de descargas activas
            delete window.activeDownloads[download_id];
            
            if (archivo) archivo.innerHTML = '<span class="status-indicator status-error"></span>Error: ' + (data.output_file || 'Error');
            if (cancelBtn) cancelBtn.style.display = 'none';
            if (descargaDiv) descargaDiv.className += ' descarga-error';
            if (stats) stats.innerText = 'Error en la descarga';
            
            let buttonsHtml = 
                '<div class="mt-2 text-danger">' + data.error + '</div>' +
                '<div class="mt-2 url-display small">' +
                    '<strong>URL:</strong> <span class="text-break">' + (data.url || 'N/A') + '</span>' +
                '</div>' +
                '<div class="mt-2">' +
                    '<button class="btn btn-warning btn-sm me-2" onclick="reintentarDescarga(\\"' + download_id + '\\")" title="Reintentar descarga">' +
                        'Reintentar' +
                    '</button>';
            
            // Añadir botón de reanudar si es posible
            if (data.can_resume) {
                buttonsHtml += 
                    '<button class="btn btn-info btn-sm me-2" onclick="reanudarDescarga(\\"' + download_id + '\\")" title="Reanudar descarga">' +
                        'Continuar' +
                    '</button>';
            }
            
            buttonsHtml += 
                    '<button class="btn btn-success btn-sm me-2" onclick="reproducirUrlActiva(\\"' + download_id + '\\")" title="Reproducir video">' +
                        'Reproducir' +
                    '</button>' +
                    '<button class="btn btn-outline-secondary btn-sm" onclick="eliminarDescargaActiva(\\"' + download_id + '\\")" title="Eliminar de la lista">' +
                        'Quitar' +
                    '</button>' +
                '</div>';
                
            let descargaElement = document.getElementById('descarga-' + download_id);
            if (descargaElement) {
                descargaElement.innerHTML += buttonsHtml;
            }
            
            // Mostrar notificación solo una vez
            const notificationKey = download_id + '_error';
            if (!notificacionesMostradas.has(notificationKey)) {
                notificacionesMostradas.add(notificationKey);
                showNotification('Error en descarga: ' + data.error, 'danger');
            }
        } else if (data.status === 'cancelled') {
            // Remover del tracking de descargas activas
            delete window.activeDownloads[download_id];
            
            if (archivo) archivo.innerHTML = '<span class="status-indicator status-cancelled"></span>Descarga cancelada';
            if (descargaDiv) descargaDiv.className = 'descarga-item descarga-cancelled';
            if (stats) stats.innerText = 'Cancelado por el usuario';
            
            // Ocultar botones de descarga activa
            let playBtn = document.getElementById('play-btn-' + download_id);
            let pauseBtn = document.getElementById('pause-btn-' + download_id);
            let cancelBtn = document.getElementById('cancel-btn-' + download_id);
            
            if (playBtn) playBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'none';
            if (cancelBtn) cancelBtn.style.display = 'none';
            
            let descargaElementCancelled = document.getElementById('descarga-' + download_id);
            if (descargaElementCancelled) {
                // Eliminar controles existentes para evitar duplicados
                const existingControls = descargaElementCancelled.querySelectorAll('.text-warning, .url-display');
                const existingButtons = descargaElementCancelled.querySelectorAll('.btn-warning, .btn-info, .btn-success, .btn-outline-secondary');
                existingControls.forEach(el => el.remove());
                existingButtons.forEach(el => {
                    if (el.id !== 'play-btn-' + download_id && el.id !== 'pause-btn-' + download_id && el.id !== 'cancel-btn-' + download_id) {
                        el.parentElement.remove(); // Remover el contenedor del botón
                    }
                });
                
                // Crear nuevos controles usando createElement
                const cancelledMessage = document.createElement('div');
                cancelledMessage.className = 'mt-2 text-warning';
                cancelledMessage.textContent = 'Descarga cancelada por el usuario';
                
                const urlDiv = document.createElement('div');
                urlDiv.className = 'mt-2 url-display small';
                urlDiv.innerHTML = '<strong>🔗 URL:</strong> <span class="text-break">' + (data.url || 'N/A') + '</span>';
                
                const buttonContainer = document.createElement('div');
                buttonContainer.className = 'mt-2';
                
                // Botón Reintentar
                const retryBtn = document.createElement('button');
                retryBtn.className = 'btn btn-warning btn-sm me-2';
                retryBtn.innerHTML = '🔄 Reintentar';
                retryBtn.title = 'Reintentar descarga';
                retryBtn.onclick = function() { reintentarDescarga(download_id); };
                buttonContainer.appendChild(retryBtn);
                
                // Botón Continuar (si es posible)
                if (data.can_resume) {
                    const continueBtn = document.createElement('button');
                    continueBtn.className = 'btn btn-info btn-sm me-2';
                    continueBtn.innerHTML = '▶️ Continuar';
                    continueBtn.title = 'Reanudar descarga';
                    continueBtn.onclick = function() { reanudarDescarga(download_id); };
                    buttonContainer.appendChild(continueBtn);
                }
                
                // Botón Reproducir
                const playBtnCancelled = document.createElement('button');
                playBtnCancelled.className = 'btn btn-success btn-sm me-2';
                playBtnCancelled.textContent = 'Reproducir';
                playBtnCancelled.title = 'Reproducir video';
                playBtnCancelled.onclick = function() { reproducirUrlActiva(download_id); };
                buttonContainer.appendChild(playBtnCancelled);
                
                // Botón Quitar
                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn btn-outline-secondary btn-sm';
                removeBtn.textContent = 'Quitar';
                removeBtn.title = 'Eliminar de la lista';
                removeBtn.onclick = function() { eliminarDescargaActiva(download_id); };
                buttonContainer.appendChild(removeBtn);
                
                // Agregar todo al elemento
                descargaElementCancelled.appendChild(cancelledMessage);
                descargaElementCancelled.appendChild(urlDiv);
                descargaElementCancelled.appendChild(buttonContainer);
            }
            
            // Mostrar notificación solo una vez
            const notificationKey = download_id + '_cancelled';
            if (!notificacionesMostradas.has(notificationKey)) {
                notificacionesMostradas.add(notificationKey);
                showNotification('Descarga cancelada', 'warning');
            }
        } else if (data.status === 'paused') {
            if (archivo) archivo.innerHTML = '<span class="status-indicator status-cancelled"></span>Descarga pausada';
            if (descargaDiv) descargaDiv.className = 'descarga-item descarga-cancelled';
            if (stats) stats.innerText = 'Pausada - se puede reanudar';
            
            // Ocultar botones de descarga activa
            let playBtn = document.getElementById('play-btn-' + download_id);
            let pauseBtn = document.getElementById('pause-btn-' + download_id);
            let cancelBtn = document.getElementById('cancel-btn-' + download_id);
            
            if (playBtn) playBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'none';
            if (cancelBtn) cancelBtn.style.display = 'none';
            
            let descargaElementPaused = document.getElementById('descarga-' + download_id);
            if (descargaElementPaused) {
                // Eliminar controles de pausa existentes para evitar duplicados
                const existingPausedControls = descargaElementPaused.querySelectorAll('.paused-controls, .text-info, .url-display');
                existingPausedControls.forEach(el => el.remove());
                
                // Crear los nuevos controles de pausa
                const pausedControlsDiv = document.createElement('div');
                pausedControlsDiv.className = 'mt-2 paused-controls';
                
                // Mensaje de pausa
                const pausedMessage = document.createElement('div');
                pausedMessage.className = 'mt-2 text-info';
                pausedMessage.textContent = 'Descarga pausada - puedes continuarla';
                
                // URL display
                const urlDiv = document.createElement('div');
                urlDiv.className = 'mt-2 url-display small';
                urlDiv.innerHTML = '<strong>URL:</strong> <span class="text-break">' + (data.url || 'N/A') + '</span>';
                
                // Botón Continuar
                const continueBtn = document.createElement('button');
                continueBtn.className = 'btn btn-info btn-sm me-2';
                continueBtn.textContent = 'Continuar';
                continueBtn.title = 'Continuar descarga';
                continueBtn.onclick = function() { reanudarDescarga(download_id); };
                
                // Botón Reproducir
                const playBtnPaused = document.createElement('button');
                playBtnPaused.className = 'btn btn-success btn-sm me-2';
                playBtnPaused.textContent = 'Reproducir';
                playBtnPaused.title = 'Reproducir video';
                playBtnPaused.onclick = function() { reproducirUrlActiva(download_id); };
                
                // Botón Quitar
                const removeBtn = document.createElement('button');
                removeBtn.className = 'btn btn-outline-secondary btn-sm';
                removeBtn.textContent = 'Quitar';
                removeBtn.title = 'Eliminar de la lista';
                removeBtn.onclick = function() { eliminarDescargaActiva(download_id); };
                
                // Agregar botones al contenedor
                pausedControlsDiv.appendChild(continueBtn);
                pausedControlsDiv.appendChild(playBtnPaused);
                pausedControlsDiv.appendChild(removeBtn);
                
                // Agregar todo al elemento
                descargaElementPaused.appendChild(pausedMessage);
                descargaElementPaused.appendChild(urlDiv);
                descargaElementPaused.appendChild(pausedControlsDiv);
            }
        }
    }).catch(error => {
        // Manejar errores del fetch silenciosamente
        // Solo logear si hay errores importantes
        if (error.message !== 'Not Found' && !error.message.includes('404')) {
            console.error('Error actualizando progreso para', download_id, ':', error);
        }
    });
}

function cancelarDescarga(download_id) {
    if (confirm('¿Estás seguro de que quieres cancelar esta descarga?')) {
        fetch('/cancelar/' + download_id, {
            method: 'POST'
        }).then(r => r.json()).then(data => {
            if (data.success) {
                let archivo = document.getElementById('archivo-' + download_id);
                if (archivo) archivo.innerText = 'Cancelando...';
            }
        });
    }
}

function eliminarArchivo(filename) {
    if (confirm('¿Estás seguro de que quieres eliminar el archivo "' + filename + '"? Esta acción no se puede deshacer.')) {
        fetch('/eliminar/' + encodeURIComponent(filename), {
            method: 'DELETE'
        }).then(r => r.json()).then(data => {
            if (data.success) {
                showNotification('Archivo eliminado correctamente', 'info');
                
                // Actualizar el historial cuando se elimine un archivo
                setTimeout(function() {
                    updateHistorial();
                }, 500);
            } else {
                alert('Error al eliminar el archivo: ' + (data.error || 'Error desconocido'));
            }
        }).catch(error => {
            alert('Error al eliminar el archivo: ' + error.message);
        });
    }
}

function eliminarDescargaActiva(download_id) {
    if (confirm('¿Quieres quitar esta descarga de la lista de descargas activas?')) {
        // Limpiar notificaciones antes de eliminar
        limpiarNotificacionesDescarga(download_id);
        
        fetch('/eliminar_descarga/' + download_id, {
            method: 'DELETE'
        }).then(r => r.json()).then(data => {
            if (data.success) {
                let elemento = document.getElementById('descarga-' + download_id);
                if (elemento) {
                    elemento.remove();
                }
                showNotification('Descarga eliminada de la lista activa', 'info');
                
                // Actualizar el historial cuando se elimine una descarga
                setTimeout(function() {
                    updateHistorial();
                }, 500);
            } else {
                alert('Error al eliminar la descarga: ' + (data.error || 'Error desconocido'));
            }
        }).catch(error => {
            alert('Error al eliminar la descarga: ' + error.message);
        });
    }
}

function reintentarDescarga(download_id) {
    fetch('/progreso/' + download_id).then(r => r.json()).then(data => {
        if (data.url && data.output_file) {
            if (confirm('¿Reintentar la descarga de "' + data.output_file + '"?')) {
                document.getElementById('m3u8-url').value = data.url;
                document.getElementById('output-name').value = data.output_file.replace('.mp4', '');
                
                fetch('/eliminar_descarga/' + download_id, {
                    method: 'DELETE'
                }).then(() => {
                    let elemento = document.getElementById('descarga-' + download_id);
                    if (elemento) {
                        elemento.remove();
                    }
                    
                    let params = 'm3u8_url=' + encodeURIComponent(data.url);
                    let outputName = data.output_file.replace('.mp4', '');
                    if (outputName) params += '&output_name=' + encodeURIComponent(outputName);
                    
                    fetch('/descargar', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: params
                    }).then(r => r.json()).then(newData => {
                        if (newData.download_id) {
                            mostrarDescargaActiva(newData.download_id, data.url);
                        } else if (newData.error) {
                            alert('Error al reintentar: ' + newData.error);
                        }
                    }).catch(error => {
                        alert('Error al reintentar: ' + error.message);
                    });
                });
            }
        } else {
            alert('No se pueden obtener los datos de la descarga para reintentar.');
        }
    }).catch(error => {
        alert('Error al obtener datos de la descarga: ' + error.message);
    });
}

function copiarUrl(url) {
    let urlToCopy = decodeURIComponent(url);
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(urlToCopy).then(function() {
            let button = event.target;
            let originalText = button.innerHTML;
            button.innerHTML = 'Copiado';
            button.disabled = true;
            setTimeout(function() {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 1500);
        }).catch(function(err) {
            copiarUrlFallback(urlToCopy);
        });
    } else {
        copiarUrlFallback(urlToCopy);
    }
}

function copiarUrlFromData(button) {
    let url = button.getAttribute('data-url');
    if (!url) {
        alert('No se encontró la URL para copiar.');
        return;
    }
    
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(url).then(function() {
            let originalText = button.innerHTML;
            button.innerHTML = 'Copiado';
            button.disabled = true;
            setTimeout(function() {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 1500);
        }).catch(function(err) {
            copiarUrlFallback(url);
        });
    } else {
        copiarUrlFallback(url);
    }
}

function reproducirUrl(url) {
    let urlToPlay = decodeURIComponent(url);
    document.getElementById('m3u8-url').value = urlToPlay;
    
    playM3U8();
    
    let button = event.target;
    let originalText = button.innerHTML;
    button.innerHTML = '🎬';
    button.disabled = true;
    setTimeout(function() {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 2000);
}

function reproducirUrlFromData(button) {
    let url = button.getAttribute('data-url');
    if (!url) {
        alert('No se encontró la URL para reproducir.');
        return;
    }
    
    document.getElementById('m3u8-url').value = url;
    
    playM3U8();
    
    let originalText = button.innerHTML;
    button.innerHTML = '🎬';
    button.disabled = true;
    setTimeout(function() {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 2000);
}

function reproducirUrlActiva(download_id) {
    const playButton = document.getElementById('play-btn-' + download_id);
    
    fetch('/progreso/' + download_id).then(r => r.json()).then(data => {
        if (data.url) {
            document.getElementById('m3u8-url').value = data.url;
            
            playM3U8();
            
            if (playButton) {
                let originalText = playButton.innerHTML;
                playButton.innerHTML = '🎬 Reproduciendo...';
                playButton.disabled = true;
                setTimeout(function() {
                    playButton.innerHTML = originalText;
                    playButton.disabled = false;
                }, 3000);
            }
            
            showNotification('Reproduciendo video en el reproductor', 'info');
        } else {
            showNotification('No se pudo obtener la URL para reproducir', 'warning');
        }
    }).catch(error => {
        showNotification('Error al obtener la URL: ' + error.message, 'danger');
    });
}

function copiarUrlFallback(url) {
    let urlToCopy = typeof url === 'string' ? decodeURIComponent(url) : url;
    
    let textArea = document.createElement('textarea');
    textArea.value = urlToCopy;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
        document.execCommand('copy');
        alert('URL copiada al portapapeles');
    } catch (err) {
        alert('No se pudo copiar la URL. Cópiala manualmente: ' + urlToCopy);
    }
    
    document.body.removeChild(textArea);
}
</script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    url = request.args.get('url', '')
    # Historial: todos los archivos MP4 en static con información adicional
    static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
    archivos = []
    if os.path.exists(static_dir):
        for f in glob.glob(os.path.join(static_dir, '*.mp4')):
            filename = os.path.basename(f)
            metadata = load_video_metadata(filename)
            file_stats = os.stat(f)
            
            archivo_info = {
                'archivo': filename,
                'tamaño': format_file_size(file_stats.st_size),
                'tamaño_bytes': file_stats.st_size,
                'fecha': format_modification_time(file_stats.st_mtime),
                'fecha_timestamp': file_stats.st_mtime,
                'url': metadata['url'] if metadata and 'url' in metadata else None
            }
            archivos.append(archivo_info)
        # Ordenar por fecha de modificación (más reciente primero)
        archivos.sort(key=lambda x: x['fecha_timestamp'], reverse=True)
    
    # Estadísticas de descargas activas
    stats = get_download_stats()
    
    return render_template_string(default_html, url=url, historial=archivos, stats=stats)

def format_file_size(size_bytes):
    """Convierte bytes a formato legible"""
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def format_modification_time(timestamp):
    """Convierte timestamp a formato legible"""
    import datetime
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime('%d/%m/%Y %H:%M')

def format_duration(seconds):
    """Convierte segundos a formato HH:MM:SS"""
    if seconds < 0:
        return "00:00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def get_download_stats():
    """Obtiene estadísticas de descargas activas"""
    downloading = sum(1 for d in multi_progress.values() if d['status'] == 'downloading')
    completed = sum(1 for d in multi_progress.values() if d['status'] == 'done')
    errors = sum(1 for d in multi_progress.values() if d['status'] == 'error')
    cancelled = sum(1 for d in multi_progress.values() if d['status'] == 'cancelled')
    
    return {
        'downloading': downloading,
        'completed': completed,
        'errors': errors,
        'cancelled': cancelled,
        'total': len(multi_progress)
    }

def is_valid_m3u8_url(url):
    """Valida si la URL es un formato M3U8 válido"""
    import re
    pattern = r'^https?://.+\.m3u8(\?.*)?$'
    return re.match(pattern, url) is not None

def sanitize_filename(filename):
    """Limpia el nombre del archivo de caracteres no seguros para Windows"""
    import re
    
    # Caracteres prohibidos en Windows: < > : " | ? * \ /
    # También eliminar caracteres de control (ASCII 0-31)
    forbidden_chars = r'[<>:"|?*\\/]'
    
    # Reemplazar caracteres prohibidos con guión bajo
    cleaned = re.sub(forbidden_chars, '_', filename)
    
    # Eliminar caracteres de control ASCII (0-31)
    cleaned = re.sub(r'[\x00-\x1f]', '', cleaned)
    
    # Eliminar espacios al inicio y final
    cleaned = cleaned.strip()
    
    # Eliminar puntos al final (Windows no los permite)
    cleaned = cleaned.rstrip('.')
    
    # Verificar nombres reservados de Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = cleaned.rsplit('.', 1)[0] if '.' in cleaned else cleaned
    if name_without_ext.upper() in reserved_names:
        cleaned = f"_{cleaned}"
    
    # Si el nombre queda vacío, usar un nombre por defecto
    if not cleaned or cleaned.isspace():
        cleaned = "video_sin_nombre"
    
    return cleaned

def extract_m3u8_metadata(m3u8_url):
    """Extrae metadatos útiles del archivo M3U8 para nombrar automáticamente"""
    import requests
    import re
    from urllib.parse import urlparse, unquote
    
    metadata = {
        'suggested_name': '',
        'resolution': '',
        'duration': 0,
        'title': '',
        'quality': '',
        'bitrate': '',
        'video_info': {}
    }
    
    try:
        # 1. Extraer información de la URL
        parsed_url = urlparse(m3u8_url)
        url_path = unquote(parsed_url.path)
        
        # Buscar nombre en la URL - incluir 'index' con información del directorio
        url_filename = url_path.split('/')[-1].replace('.m3u8', '')
        if url_filename and url_filename != 'playlist':
            if url_filename == 'index':
                # Para archivos index, usar el nombre del directorio padre
                path_parts = [p for p in url_path.split('/') if p and p != 'index.m3u8']
                if path_parts:
                    metadata['suggested_name'] = sanitize_filename(path_parts[-1])
            else:
                metadata['suggested_name'] = sanitize_filename(url_filename)
        
        # 2. Descargar y analizar el contenido M3U8
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/vnd.apple.mpegurl, application/x-mpegurl, application/octet-stream, */*',
            'Referer': f"{parsed_url.scheme}://{parsed_url.netloc}/"
        }
        
        try:
            response = requests.get(m3u8_url, headers=headers, timeout=15)
            response.raise_for_status()
            content = response.text
            
            # Verificar que el contenido parece ser un M3U8 válido
            if not content.strip().startswith('#EXTM3U') and '#EXTINF:' not in content:
                print(f"Advertencia: El contenido no parece ser un M3U8 válido para {m3u8_url}")
                # Aún así continuar, puede ser un formato válido
            
        except requests.RequestException as e:
            print(f"Error descargando M3U8 para metadatos: {e}")
            # Fallback: usar solo la información de la URL
            if not metadata['suggested_name']:
                try:
                    # Intentar extraer nombre del directorio padre
                    path_parts = [p for p in parsed_url.path.split('/') if p and '.m3u8' not in p]
                    if path_parts:
                        metadata['suggested_name'] = sanitize_filename(path_parts[-1])
                except:
                    pass
            return metadata
        
        # 3. Extraer información del contenido M3U8
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extraer resolución
            if 'RESOLUTION=' in line:
                resolution_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                if resolution_match:
                    resolution = resolution_match.group(1)
                    metadata['resolution'] = resolution
                    # Determinar calidad basada en resolución
                    height = int(resolution.split('x')[1])
                    if height >= 1080:
                        metadata['quality'] = '1080p'
                    elif height >= 720:
                        metadata['quality'] = '720p'
                    elif height >= 480:
                        metadata['quality'] = '480p'
                    else:
                        metadata['quality'] = f'{height}p'
            
            # Extraer bitrate
            if 'BANDWIDTH=' in line:
                bitrate_match = re.search(r'BANDWIDTH=(\d+)', line)
                if bitrate_match:
                    bitrate = int(bitrate_match.group(1))
                    metadata['bitrate'] = f"{bitrate // 1000}kbps"
            
            # Extraer título de segmentos
            if line.startswith('#EXTINF:') and ',' in line:
                title_part = line.split(',', 1)[1].strip()
                if title_part and title_part not in ['', 'no desc']:
                    metadata['title'] = sanitize_filename(title_part)
            
            # Extraer duración total aproximada
            if line.startswith('#EXT-X-TARGETDURATION:'):
                duration_match = re.search(r'#EXT-X-TARGETDURATION:(\d+)', line)
                if duration_match:
                    metadata['duration'] = int(duration_match.group(1))
        
        # 4. Generar nombre sugerido inteligente
        name_parts = []
        
        # Usar título si existe
        if metadata['title']:
            name_parts.append(metadata['title'])
        elif metadata['suggested_name']:
            name_parts.append(metadata['suggested_name'])
        else:
            # Generar nombre basado en la URL
            domain = parsed_url.netloc
            if domain:
                clean_domain = domain.replace('www.', '').split('.')[0]
                name_parts.append(clean_domain)
        
        # Añadir calidad si se detectó
        if metadata['quality']:
            name_parts.append(metadata['quality'])
        
        # Generar nombre final
        if name_parts:
            suggested_name = '_'.join(name_parts)
            # Limpiar y limitar longitud
            suggested_name = re.sub(r'[^\w\-_\.]', '_', suggested_name)
            suggested_name = re.sub(r'_+', '_', suggested_name)  # Eliminar múltiples guiones bajos
            metadata['suggested_name'] = suggested_name[:50]  # Limitar a 50 caracteres
        
        # 5. Información adicional
        metadata['video_info'] = {
            'source_domain': parsed_url.netloc,
            'estimated_segments': content.count('#EXTINF:'),
            'is_live': '#EXT-X-ENDLIST' not in content,
            'version': '3' if '#EXT-X-VERSION:3' in content else 'unknown'
        }
        
    except requests.RequestException as e:
        print(f"Error descargando M3U8 para metadatos: {e}")
        # Fallback: usar solo la URL
        try:
            parsed_url = urlparse(m3u8_url)
            url_filename = parsed_url.path.split('/')[-1].replace('.m3u8', '')
            if url_filename:
                metadata['suggested_name'] = sanitize_filename(url_filename)
        except:
            pass
    except Exception as e:
        print(f"Error procesando metadatos M3U8: {e}")
    
    return metadata

def suggest_filename_from_m3u8(m3u8_url):
    """Función simplificada para obtener nombre sugerido"""
    metadata = extract_m3u8_metadata(m3u8_url)
    
    if metadata['suggested_name']:
        return metadata['suggested_name']
    
    # Fallback: generar nombre único
    return f'video_{uuid.uuid4().hex[:8]}'

def suggest_filename_from_url_only(m3u8_url):
    """Función de fallback que solo usa la URL sin hacer peticiones HTTP"""
    import re
    from urllib.parse import urlparse, unquote
    
    try:
        parsed_url = urlparse(m3u8_url)
        url_path = unquote(parsed_url.path)
        
        # Extraer nombre del archivo o directorio
        url_filename = url_path.split('/')[-1].replace('.m3u8', '')
        
        if url_filename and url_filename != 'playlist':
            if url_filename == 'index':
                # Para archivos index, usar el nombre del directorio padre
                path_parts = [p for p in url_path.split('/') if p and p != 'index.m3u8']
                if path_parts:
                    return sanitize_filename(path_parts[-1])
            else:
                return sanitize_filename(url_filename)
        
        # Si no se puede extraer nombre, usar dominio + timestamp
        domain = parsed_url.netloc.replace('www.', '').split('.')[0]
        timestamp = str(int(time.time()))[-6:]  # Últimos 6 dígitos
        return f"{domain}_{timestamp}"
        
    except Exception:
        # Fallback final: nombre único
        return f'video_{uuid.uuid4().hex[:8]}'

def cleanup_old_downloads():
    """Limpia descargas antiguas del diccionario de progreso"""
    current_time = time.time()
    to_remove = []
    
    for download_id, progress in multi_progress.items():
        # Remover descargas completadas o con error después de 1 hora
        if progress['status'] in ['done', 'error', 'cancelled']:
            if 'end_time' in progress and current_time - progress['end_time'] > 3600:
                to_remove.append(download_id)
            elif 'start_time' in progress and current_time - progress['start_time'] > 7200:
                to_remove.append(download_id)
    
    for download_id in to_remove:
        del multi_progress[download_id]
        cancelled_downloads.discard(download_id)

# Llamar cleanup cada vez que se carga la página principal
def periodic_cleanup():
    """Ejecuta limpieza periódica en un hilo separado"""
    import threading
    import time
    
    def cleanup_worker():
        while True:
            time.sleep(300)  # 5 minutos
            cleanup_old_downloads()
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

# Iniciar limpieza periódica al inicio
periodic_cleanup()

def save_video_metadata(filename, url):
    """Guarda metadatos del video en un archivo JSON"""
    import json
    import datetime
    
    static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
    metadata_file = os.path.join(static_dir, f"{filename}.meta")
    
    metadata = {
        'url': url,
        'download_date': datetime.datetime.now().isoformat(),
        'filename': filename
    }
    
    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error al guardar metadatos para {filename}: {e}")

def load_video_metadata(filename):
    """Carga metadatos del video desde el archivo JSON"""
    import json
    
    static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
    metadata_file = os.path.join(static_dir, f"{filename}.meta")
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al leer metadatos para {filename}: {e}")
    
    return None

@app.route('/descargar', methods=['POST'])
def descargar():
    # Verificar límite de descargas concurrentes
    active_downloads = sum(1 for d in multi_progress.values() if d['status'] == 'downloading')
    if active_downloads >= MAX_CONCURRENT_DOWNLOADS:
        return jsonify({
            'error': f'Máximo {MAX_CONCURRENT_DOWNLOADS} descargas simultáneas permitidas. Espera a que termine alguna.'
        }), 429
    
    m3u8_url = request.form.get('m3u8_url', '').strip()
    output_name = request.form.get('output_name', '').strip()
    quality = request.form.get('quality', DEFAULT_QUALITY).strip()
    resume_id = request.form.get('resume_id', '').strip()  # Para reanudar
    
    # Validaciones de entrada
    if not m3u8_url:
        return jsonify({'error': 'URL M3U8 no proporcionada'}), 400
    
    if not is_valid_m3u8_url(m3u8_url):
        return jsonify({'error': 'URL M3U8 no válida'}), 400
    
    # Si es una reanudación, usar el ID existente
    if resume_id and resume_id in multi_progress:
        download_id = resume_id
        output_file = multi_progress[download_id]['output_file']
        multi_progress[download_id]['status'] = 'downloading'
        multi_progress[download_id]['can_resume'] = False
    else:
        # Procesar nombre del archivo
        if output_name:
            output_name = sanitize_filename(output_name)
            if not output_name.lower().endswith('.mp4'):
                output_name += '.mp4'
            output_file = output_name
        else:
            # Intentar extraer nombre inteligente del M3U8
            try:
                suggested_name = suggest_filename_from_m3u8(m3u8_url)
                if suggested_name and suggested_name != f'video_{uuid.uuid4().hex[:8]}':
                    output_file = f'{suggested_name}.mp4'
                else:
                    output_file = f'video_{uuid.uuid4().hex[:8]}.mp4'
            except Exception as e:
                print(f"Error extrayendo nombre de M3U8: {e}")
                output_file = f'video_{uuid.uuid4().hex[:8]}.mp4'
        
        # Verificar si el archivo ya existe
        static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
        if os.path.exists(os.path.join(static_dir, output_file)):
            base_name = output_file[:-4]  # Sin .mp4
            counter = 1
            while os.path.exists(os.path.join(static_dir, f"{base_name}_{counter}.mp4")):
                counter += 1
            output_file = f"{base_name}_{counter}.mp4"
        
        # Crear nuevo download_id
        download_id = uuid.uuid4().hex[:8]
        
        # Crear ID único para la descarga
        multi_progress[download_id] = {
            'total': 0,
            'current': 0,
            'status': 'downloading',
            'error': '',
            'porcentaje': 0,
            'output_file': output_file,
            'url': m3u8_url,
            'quality': quality,
            'start_time': time.time(),
            'can_resume': False,
            'downloaded_segments': [],
            'bytes_downloaded': 0,
            'download_speed': 0.0,  # Inicializado como float
            'last_update_time': time.time(),
            'last_bytes': 0,
            'elapsed_time': 0,  # Tiempo transcurrido en segundos
            'estimated_time': 0,  # Tiempo estimado restante en segundos
            'total_time': 0  # Tiempo total cuando termine
        }
    
    def run_download():
        # Crear directorio temporal único para esta descarga (fuera del try)
        temp_dir = os.path.join(os.path.dirname(__file__), TEMP_DIR, download_id)
        
        try:
            # Verificar si ya fue cancelado antes de empezar
            if download_id in cancelled_downloads:
                multi_progress[download_id]['status'] = 'cancelled'
                save_download_state()
                return
                
            # Crear el directorio temporal
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            original_dir = os.getcwd()
            
            # Descarga de segmentos con directorio específico y calidad optimizada
            downloader = M3U8Downloader(
                m3u8_url=m3u8_url, 
                output_filename=output_file, 
                max_workers=1000,  # EXTREMO para internet súper rápido
                temp_dir=temp_dir
            )
            segment_urls = downloader._get_segment_urls()
            multi_progress[download_id]['total'] = len(segment_urls)
            
            # Obtener segmentos ya descargados para reanudación
            downloaded_segments = multi_progress[download_id].get('downloaded_segments', [])
            start_index = len(downloaded_segments)
            
            for i, url in enumerate(segment_urls):
                # Verificar cancelación en cada iteración
                if download_id in cancelled_downloads:
                    multi_progress[download_id]['status'] = 'cancelled'
                    multi_progress[download_id]['error'] = 'Descarga cancelada por el usuario'
                    multi_progress[download_id]['can_resume'] = True
                    save_download_state()
                    return
                
                # Saltar segmentos ya descargados
                if i < start_index:
                    multi_progress[download_id]['current'] = i + 1
                    continue
                    
                try:
                    # Obtener tiempo antes de la descarga
                    segment_start_time = time.time()
                    
                    # Descargar segmento y obtener tamaño
                    result = downloader._download_segment(url, i)
                    
                    # Verificar que el resultado es válido
                    if not result:
                        raise Exception("No se pudo descargar el segmento")
                    
                    segment_name, bytes_downloaded = result
                    
                    seg_path = os.path.join(temp_dir, f'segment_{i:05d}.ts')
                    if not os.path.exists(seg_path):
                        raise FileNotFoundError(f"No se encontró el archivo {seg_path} tras la descarga.")
                    
                    # Calcular velocidad de descarga
                    current_time = time.time()
                    time_diff = current_time - multi_progress[download_id]['last_update_time']
                    
                    # Calcular tiempo transcurrido
                    elapsed_time = current_time - multi_progress[download_id]['start_time']
                    multi_progress[download_id]['elapsed_time'] = elapsed_time
                    
                    if time_diff > 0 and isinstance(bytes_downloaded, (int, float)) and bytes_downloaded > 0:
                        # Actualizar bytes totales descargados
                        multi_progress[download_id]['bytes_downloaded'] += bytes_downloaded
                        
                        # Calcular velocidad en MB/s
                        segment_duration = current_time - segment_start_time
                        if segment_duration > 0:
                            bytes_per_second = bytes_downloaded / segment_duration
                            speed_mbps = bytes_per_second / (1024 * 1024)  # Convertir a MB/s
                            
                            # Usar promedio móvil para suavizar la velocidad
                            current_speed = multi_progress[download_id]['download_speed']
                            if current_speed == 0:
                                multi_progress[download_id]['download_speed'] = speed_mbps
                            else:
                                # Promedio móvil con factor 0.3 para suavizar
                                multi_progress[download_id]['download_speed'] = (current_speed * 0.7) + (speed_mbps * 0.3)
                            
                            # Calcular tiempo estimado restante
                            segments_remaining = len(segment_urls) - (i + 1)
                            if segments_remaining > 0 and multi_progress[download_id]['download_speed'] > 0:
                                # Estimar bytes promedio por segmento
                                avg_bytes_per_segment = multi_progress[download_id]['bytes_downloaded'] / (i + 1 - start_index) if (i + 1 - start_index) > 0 else bytes_downloaded
                                estimated_bytes_remaining = segments_remaining * avg_bytes_per_segment
                                estimated_seconds = estimated_bytes_remaining / (multi_progress[download_id]['download_speed'] * 1024 * 1024)
                                multi_progress[download_id]['estimated_time'] = estimated_seconds
                            else:
                                multi_progress[download_id]['estimated_time'] = 0
                        
                        multi_progress[download_id]['last_update_time'] = current_time
                    
                    # Marcar segmento como descargado
                    multi_progress[download_id]['downloaded_segments'].append(i)
                    
                except Exception as err:
                    multi_progress[download_id]['error'] = f"Error al descargar el segmento {i+1}: {err}"
                    multi_progress[download_id]['status'] = 'error'
                    multi_progress[download_id]['can_resume'] = True
                    save_download_state()
                    break
                    
                porcentaje = int(((i + 1) / len(segment_urls)) * 100) if len(segment_urls) > 0 else 0
                multi_progress[download_id]['current'] = i + 1
                multi_progress[download_id]['porcentaje'] = porcentaje
                
                # Guardar estado cada 10 segmentos
                if (i + 1) % 10 == 0:
                    save_download_state()
                
            # Verificar cancelación antes de la fusión
            if download_id in cancelled_downloads:
                multi_progress[download_id]['status'] = 'cancelled'
                multi_progress[download_id]['error'] = 'Descarga cancelada por el usuario'
                multi_progress[download_id]['can_resume'] = True
                save_download_state()
                return
                
            # Fusión y movimiento del archivo MP4
            if multi_progress[download_id]['status'] == 'downloading':
                segment_files = [f'segment_{i:05d}.ts' for i in range(len(segment_urls))]
                downloader._merge_segments(segment_files)
                static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
                if not os.path.exists(static_dir):
                    os.makedirs(static_dir)
                static_path = os.path.join(static_dir, output_file)
                output_path = os.path.abspath(os.path.join(original_dir, output_file))
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    os.replace(output_path, static_path)
                    multi_progress[download_id]['status'] = 'done'
                    multi_progress[download_id]['end_time'] = time.time()
                    multi_progress[download_id]['total_time'] = multi_progress[download_id]['end_time'] - multi_progress[download_id]['start_time']
                    multi_progress[download_id]['can_resume'] = False
                    
                    # Guardar metadatos del video (URL y fecha de descarga)
                    try:
                        save_video_metadata(output_file, m3u8_url)
                    except Exception as meta_error:
                        print(f"Error al guardar metadatos: {meta_error}")
                else:
                    multi_progress[download_id]['status'] = 'error'
                    multi_progress[download_id]['error'] = 'No se pudo descargar el video o el archivo está vacío.'
                    multi_progress[download_id]['can_resume'] = True
                    
        except Exception as e:
            multi_progress[download_id]['status'] = 'error'
            multi_progress[download_id]['error'] = str(e)
            multi_progress[download_id]['can_resume'] = True
        finally:
            # Guardar estado final
            save_download_state()
            
            # Limpiar el directorio temporal específico de esta descarga
            try:
                if os.path.exists(temp_dir) and multi_progress[download_id]['status'] == 'done':
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Error al limpiar directorio temporal {temp_dir}: {cleanup_error}")
            
            # Limpiar el ID de cancelación cuando termine la descarga
            cancelled_downloads.discard(download_id)
    
    thread = threading.Thread(target=run_download)
    thread.start()
    save_download_state()
    return jsonify({'download_id': download_id}), 202

@app.route('/progreso/<download_id>', methods=['GET'])
def progreso(download_id):
    if download_id not in multi_progress:
        return jsonify({'status': 'error', 'error': 'ID de descarga no encontrado.'}), 404
    
    progress_data = multi_progress[download_id].copy()
    
    # Añadir tiempos formateados
    progress_data['elapsed_time_formatted'] = format_duration(progress_data.get('elapsed_time', 0))
    progress_data['estimated_time_formatted'] = format_duration(progress_data.get('estimated_time', 0))
    progress_data['total_time_formatted'] = format_duration(progress_data.get('total_time', 0))
    
    return jsonify(progress_data), 200

@app.route('/cancelar/<download_id>', methods=['POST'])
def cancelar_descarga(download_id):
    if download_id not in multi_progress:
        return jsonify({'success': False, 'error': 'ID de descarga no encontrado.'}), 404
    
    # Marcar la descarga como cancelada
    cancelled_downloads.add(download_id)
    multi_progress[download_id]['status'] = 'cancelled'
    multi_progress[download_id]['error'] = 'Descarga cancelada por el usuario'
    
    return jsonify({'success': True}), 200

@app.route('/eliminar/<filename>', methods=['DELETE'])
def eliminar_archivo(filename):
    try:
        # Validar que el nombre del archivo sea seguro
        import re
        if not re.match(r'^[a-zA-Z0-9_\-\. ]+\.mp4$', filename):
            return jsonify({'success': False, 'error': 'Nombre de archivo no válido.'}), 400
        
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        file_path = os.path.join(static_dir, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'El archivo no existe.'}), 404
        
        # Verificar que el archivo está en el directorio static (seguridad)
        if not os.path.abspath(file_path).startswith(os.path.abspath(static_dir)):
            return jsonify({'success': False, 'error': 'Ruta de archivo no válida.'}), 400
        
        # Eliminar el archivo
        os.remove(file_path)
        
        # También eliminar el archivo de metadatos si existe
        metadata_file = os.path.join(static_dir, f"{filename}.meta")
        if os.path.exists(metadata_file):
            try:
                os.remove(metadata_file)
            except Exception as meta_error:
                print(f"Error al eliminar metadatos para {filename}: {meta_error}")
        
        return jsonify({'success': True, 'message': f'Archivo {filename} eliminado correctamente.'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error al eliminar el archivo: {str(e)}'}), 500

@app.route('/eliminar_descarga/<download_id>', methods=['DELETE'])
def eliminar_descarga_activa(download_id):
    """Elimina una descarga activa del registro de progreso"""
    try:
        if download_id not in multi_progress:
            return jsonify({'success': False, 'error': 'ID de descarga no encontrado.'}), 404
        
        # Cancelar primero si está activa
        if multi_progress[download_id]['status'] == 'downloading':
            cancelled_downloads.add(download_id)
            multi_progress[download_id]['status'] = 'cancelled'
        
        # Remover del registro de progreso
        del multi_progress[download_id]
        
        # Remover de cancelaciones si existe
        cancelled_downloads.discard(download_id)
        
        # Guardar estado
        save_download_state()
        
        return jsonify({'success': True, 'message': 'Descarga eliminada del registro.'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error al eliminar descarga: {str(e)}'}), 500

@app.route('/reanudar/<download_id>', methods=['POST'])
def reanudar_descarga(download_id):
    """Reanuda una descarga pausada o con error"""
    if download_id not in multi_progress:
        return jsonify({'success': False, 'error': 'ID de descarga no encontrado.'}), 404
    
    download_info = multi_progress[download_id]
    
    if not download_info.get('can_resume', False):
        return jsonify({'success': False, 'error': 'Esta descarga no se puede reanudar.'}), 400
    
    if download_info['status'] == 'downloading':
        return jsonify({'success': False, 'error': 'La descarga ya está en progreso.'}), 400
    
    # Verificar límite de descargas concurrentes
    active_downloads = sum(1 for d in multi_progress.values() if d['status'] == 'downloading')
    if active_downloads >= MAX_CONCURRENT_DOWNLOADS:
        return jsonify({
            'success': False,
            'error': f'Máximo {MAX_CONCURRENT_DOWNLOADS} descargas simultáneas permitidas.'
        }), 429
    
    # Iniciar descarga con reanudación
    try:
        params = {
            'm3u8_url': download_info['url'],
            'output_name': download_info['output_file'].replace('.mp4', ''),
            'quality': download_info.get('quality', DEFAULT_QUALITY),
            'resume_id': download_id
        }
        
        # Simular la llamada POST interna
        with app.test_request_context('/descargar', method='POST', data=params):
            result = descargar()
            
        return jsonify({'success': True, 'message': 'Descarga reanudada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/pausar/<download_id>', methods=['POST'])
def pausar_descarga(download_id):
    """Pausa una descarga en progreso"""
    if download_id not in multi_progress:
        return jsonify({'success': False, 'error': 'ID de descarga no encontrado.'}), 404
    
    download_info = multi_progress[download_id]
    
    if download_info['status'] != 'downloading':
        return jsonify({'success': False, 'error': 'Solo se pueden pausar descargas en progreso.'}), 400
    
    try:
        # Marcar la descarga como pausada
        download_info['status'] = 'paused'
        download_info['can_resume'] = True
        download_info['pause_time'] = time.time()
        
        # Añadir a cancelled_downloads para detener el proceso
        cancelled_downloads.add(download_id)
        
        # Guardar estado
        save_download_state()
        
        return jsonify({
            'success': True, 
            'message': 'Descarga pausada correctamente',
            'status': 'paused'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/renombrar/<filename>', methods=['POST'])
def renombrar_archivo(filename):
    """Renombra un archivo descargado"""
    try:
        data = request.get_json()
        nuevo_nombre = data.get('nuevo_nombre', '').strip()
        
        if not nuevo_nombre:
            return jsonify({'success': False, 'error': 'Nuevo nombre no proporcionado.'}), 400
        
        print(f"🔄 Renombrando '{filename}' a '{nuevo_nombre}'")
        
        # Sanitizar el nuevo nombre
        nuevo_nombre_limpio = sanitize_filename(nuevo_nombre)
        print(f"📝 Nombre sanitizado: '{nuevo_nombre_limpio}'")
        
        if not nuevo_nombre_limpio.lower().endswith('.mp4'):
            nuevo_nombre_limpio += '.mp4'
        
        # Validar que el nuevo nombre es válido
        if len(nuevo_nombre_limpio) > 255:
            return jsonify({'success': False, 'error': 'El nombre del archivo es demasiado largo (máximo 255 caracteres).'}), 400
        
        # Validar que el archivo original existe
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        archivo_original = os.path.join(static_dir, filename)
        
        print(f"📂 Verificando archivo original: {archivo_original}")
        
        if not os.path.exists(archivo_original):
            return jsonify({'success': False, 'error': f'El archivo "{filename}" no existe en el directorio static.'}), 404
        
        # Verificar que el nuevo nombre no existe
        archivo_nuevo = os.path.join(static_dir, nuevo_nombre_limpio)
        print(f"📂 Archivo destino: {archivo_nuevo}")
        
        if os.path.exists(archivo_nuevo):
            return jsonify({'success': False, 'error': f'Ya existe un archivo con el nombre "{nuevo_nombre_limpio}".'}), 400
        
        # Verificar permisos de escritura
        try:
            import tempfile
            test_file = os.path.join(static_dir, f"test_permisos_{int(time.time())}.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as perm_error:
            return jsonify({'success': False, 'error': f'Sin permisos de escritura en el directorio: {str(perm_error)}'}), 500
        
        # Renombrar el archivo
        try:
            os.rename(archivo_original, archivo_nuevo)
            print(f"✅ Archivo renombrado exitosamente")
        except OSError as os_error:
            error_msg = f"Error del sistema al renombrar: {str(os_error)}"
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
        
        # Renombrar también el archivo de metadatos si existe
        metadata_original = os.path.join(static_dir, f"{filename}.meta")
        metadata_nuevo = os.path.join(static_dir, f"{nuevo_nombre_limpio}.meta")
        
        print(f"🔍 Verificando metadatos:")
        print(f"   📋 Archivo original: {metadata_original}")
        print(f"   📋 Archivo nuevo: {metadata_nuevo}")
        print(f"   📋 Existe original: {os.path.exists(metadata_original)}")
        
        if os.path.exists(metadata_original):
            try:
                print(f"🔄 Iniciando proceso de metadatos...")
                
                # Cargar metadatos existentes
                metadata = load_video_metadata(filename)
                print(f"📋 Metadatos cargados: {metadata}")
                
                if metadata:
                    print(f"📝 URL original: {metadata.get('url', 'NO ENCONTRADA')}")
                    
                    # Actualizar solo el nombre, preservando toda la demás información
                    metadata['filename'] = nuevo_nombre_limpio
                    # Agregar información de renombrado
                    metadata['renamed_from'] = filename
                    metadata['rename_date'] = time.strftime('%Y-%m-%dT%H:%M:%S')
                    
                    print(f"📝 Metadatos actualizados: {metadata}")
                    
                    # Guardar metadatos actualizados
                    with open(metadata_nuevo, 'w', encoding='utf-8') as f:
                        import json
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ Archivo de metadatos nuevo creado: {metadata_nuevo}")
                    
                    # Verificar que se escribió correctamente
                    if os.path.exists(metadata_nuevo):
                        with open(metadata_nuevo, 'r', encoding='utf-8') as f:
                            verificacion = json.load(f)
                            print(f"🔍 Verificación - URL: {verificacion.get('url', 'NO ENCONTRADA')}")
                    
                    # Eliminar archivo de metadatos original
                    os.remove(metadata_original)
                    print(f"🗑️ Archivo de metadatos original eliminado: {metadata_original}")
                    
                    # Verificar que la URL se preservó
                    if 'url' in metadata:
                        print(f"📋 URL preservada en memoria: {metadata['url']}")
                else:
                    print(f"⚠️ No se pudieron cargar los metadatos de {filename}")
                    
            except Exception as meta_error:
                print(f"⚠️ Error al actualizar metadatos: {meta_error}")
                import traceback
                print(f"Traceback completo: {traceback.format_exc()}")
        else:
            print(f"⚠️ No existe archivo de metadatos para: {filename}")
        
        return jsonify({
            'success': True, 
            'message': f'Archivo renombrado de "{filename}" a "{nuevo_nombre_limpio}"',
            'nuevo_nombre': nuevo_nombre_limpio
        })
        
    except Exception as e:
        error_msg = f'Error al renombrar: {str(e)}'
        print(f"❌ {error_msg}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/renombrar_descarga_activa/<download_id>', methods=['POST'])
def renombrar_descarga_activa(download_id):
    """Renombra una descarga activa mientras se está descargando"""
    try:
        data = request.get_json()
        nuevo_nombre = data.get('nuevo_nombre', '').strip()
        
        if not nuevo_nombre:
            return jsonify({'success': False, 'error': 'Nuevo nombre no proporcionado.'}), 400
        
        print(f"🔄 Renombrando descarga activa '{download_id}' a '{nuevo_nombre}'")
        
        # Verificar que la descarga existe
        if download_id not in multi_progress:
            return jsonify({'success': False, 'error': 'ID de descarga no encontrado.'}), 404
        
        download_info = multi_progress[download_id]
        
        # Sanitizar el nuevo nombre
        nuevo_nombre_limpio = sanitize_filename(nuevo_nombre)
        print(f"📝 Nombre sanitizado: '{nuevo_nombre_limpio}'")
        
        if not nuevo_nombre_limpio.lower().endswith('.mp4'):
            nuevo_nombre_limpio += '.mp4'
        
        # Validar que el nuevo nombre es válido
        if len(nuevo_nombre_limpio) > 255:
            return jsonify({'success': False, 'error': 'El nombre del archivo es demasiado largo (máximo 255 caracteres).'}), 400
        
        # Verificar que el nuevo nombre no existe en static
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        archivo_nuevo = os.path.join(static_dir, nuevo_nombre_limpio)
        
        if os.path.exists(archivo_nuevo):
            return jsonify({'success': False, 'error': f'Ya existe un archivo con el nombre "{nuevo_nombre_limpio}".'}), 400
        
        # Actualizar la información de la descarga
        download_info['output_file'] = nuevo_nombre_limpio
        download_info['original_filename'] = nuevo_nombre_limpio
        
        # Si hay un downloader activo, también actualizar su output_file
        if 'downloader' in download_info and download_info['downloader']:
            try:
                # El M3U8Downloader tiene un atributo output_file que podemos actualizar
                downloader = download_info['downloader']
                if hasattr(downloader, 'output_file'):
                    old_output_path = downloader.output_file
                    new_output_path = os.path.join(static_dir, nuevo_nombre_limpio)
                    downloader.output_file = new_output_path
                    print(f"✅ Actualizado output_file del downloader: {new_output_path}")
                    
                    # Si ya existe un archivo temporal parcial, renombrarlo
                    if os.path.exists(old_output_path) and old_output_path != new_output_path:
                        try:
                            os.rename(old_output_path, new_output_path)
                            print(f"✅ Archivo temporal renombrado de {old_output_path} a {new_output_path}")
                        except OSError as rename_error:
                            print(f"⚠️ No se pudo renombrar archivo temporal: {rename_error}")
                            
            except Exception as downloader_error:
                print(f"⚠️ Error al actualizar downloader: {downloader_error}")
        
        # Guardar el estado actualizado
        save_download_state()
        
        # Actualizar metadatos si ya existen o crear nuevos
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        metadata_nuevo = os.path.join(static_dir, f"{nuevo_nombre_limpio}.meta")
        
        try:
            # Crear o actualizar metadatos con la información de la descarga activa
            metadata = {
                'url': download_info.get('url', ''),
                'download_date': download_info.get('start_time', ''),
                'filename': nuevo_nombre_limpio,
                'download_id': download_id,
                'status': download_info.get('status', 'downloading')
            }
            
            # Si ya existe un archivo de metadatos, preservar información adicional
            if os.path.exists(metadata_nuevo):
                try:
                    existing_metadata = load_video_metadata(nuevo_nombre_limpio)
                    if existing_metadata:
                        # Preservar datos existentes y actualizar con nuevos
                        existing_metadata.update(metadata)
                        metadata = existing_metadata
                        print(f"📋 Metadatos existentes preservados y actualizados")
                except Exception as load_error:
                    print(f"⚠️ Error al cargar metadatos existentes: {load_error}")
            
            # Guardar metadatos actualizados
            with open(metadata_nuevo, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Metadatos guardados: {metadata_nuevo}")
            
        except Exception as meta_error:
            print(f"⚠️ Error al actualizar metadatos de descarga activa: {meta_error}")
        
        print(f"✅ Descarga activa renombrada exitosamente a: {nuevo_nombre_limpio}")
        
        return jsonify({
            'success': True, 
            'message': f'Descarga renombrada de "{download_info.get("original_filename", "archivo")}" a "{nuevo_nombre_limpio}"',
            'nuevo_nombre': nuevo_nombre_limpio.replace('.mp4', ''),
            'download_id': download_id
        })
        
    except Exception as e:
        error_msg = f'Error al renombrar descarga activa: {str(e)}'
        print(f"❌ {error_msg}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/static/<path:filename>', methods=['GET'])
def serve_static(filename):
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_file(os.path.join(static_dir, filename))

@app.route('/favicon.ico')
def favicon():
    # Devolver un favicon básico o un 204 No Content
    from flask import Response
    return Response(status=204)

@app.route('/api/stats', methods=['GET'])
def get_api_stats():
    """Endpoint para obtener estadísticas detalladas de la aplicación"""
    try:
        static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
        total_files = 0
        total_size = 0
        
        if os.path.exists(static_dir):
            for f in glob.glob(os.path.join(static_dir, '*.mp4')):
                total_files += 1
                total_size += os.path.getsize(f)
        
        download_stats = get_download_stats()
        
        return jsonify({
            'success': True,
            'data': {
                'total_downloads': total_files,
                'total_size_bytes': total_size,
                'total_size_formatted': format_file_size(total_size),
                'active_downloads': download_stats,
                'timestamp': time.time()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_videos():
    """Endpoint para búsqueda avanzada de videos"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        filters = data.get('filters', {})
        
        static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
        results = []
        
        if os.path.exists(static_dir):
            for f in glob.glob(os.path.join(static_dir, '*.mp4')):
                filename = os.path.basename(f)
                file_stats = os.stat(f)
                metadata = load_video_metadata(filename)
                
                # Aplicar filtros de búsqueda
                if query and query not in filename.lower():
                    continue
                
                # Filtros adicionales
                if filters.get('min_size') and file_stats.st_size < filters['min_size']:
                    continue
                    
                if filters.get('max_size') and file_stats.st_size > filters['max_size']:
                    continue
                
                results.append({
                    'filename': filename,
                    'size': file_stats.st_size,
                    'size_formatted': format_file_size(file_stats.st_size),
                    'date': file_stats.st_mtime,
                    'date_formatted': format_modification_time(file_stats.st_mtime),
                    'url': metadata['url'] if metadata and 'url' in metadata else None
                })
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """Endpoint para manejar configuraciones de usuario"""
    global MAX_CONCURRENT_DOWNLOADS
    
    if request.method == 'GET':
        # Devolver configuración predeterminada
        return jsonify({
            'success': True,
            'config': {
                'max_concurrent_downloads': MAX_CONCURRENT_DOWNLOADS,
                'auto_download': False,
                'notifications': True,
                'quality': 'auto'
            }
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            # Aquí podrías guardar las configuraciones en una base de datos
            # Por ahora solo validamos y devolvemos éxito
            
            if 'max_concurrent_downloads' in data:
                MAX_CONCURRENT_DOWNLOADS = max(1, min(10, int(data['max_concurrent_downloads'])))
            
            return jsonify({'success': True, 'message': 'Configuración actualizada'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Método no permitido'}), 405

@app.route('/api/queue', methods=['GET', 'POST', 'DELETE'])
def handle_download_queue():
    """Endpoint para manejar la cola de descargas"""
    global download_queue_storage, queue_running
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'queue': download_queue_storage,
            'running': queue_running,
            'count': len(download_queue_storage)
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            action = data.get('action', 'add')
            
            if action == 'add':
                url = data.get('url', '').strip()
                name = data.get('name', '').strip()
                quality = data.get('quality', DEFAULT_QUALITY)
                
                if not url or not is_valid_m3u8_url(url):
                    return jsonify({'success': False, 'error': 'URL M3U8 no válida'}), 400
                
                item = {
                    'id': str(uuid.uuid4()),
                    'url': url,
                    'name': name if name else f'video_{uuid.uuid4().hex[:8]}',
                    'quality': quality,
                    'status': 'pending',
                    'added_time': time.time()
                }
                
                download_queue_storage.append(item)
                save_download_state()
                
                return jsonify({
                    'success': True, 
                    'message': 'URL añadida a la cola',
                    'item': item
                })
            
            elif action == 'start':
                queue_running = True
                save_download_state()
                # Iniciar procesamiento en un hilo separado
                threading.Thread(target=process_download_queue, daemon=True).start()
                return jsonify({'success': True, 'message': 'Cola iniciada'})
            
            elif action == 'stop':
                queue_running = False
                save_download_state()
                return jsonify({'success': True, 'message': 'Cola detenida'})
            
            else:
                return jsonify({'success': False, 'error': 'Acción no válida'}), 400
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            item_id = data.get('id')
            
            if not item_id:
                return jsonify({'success': False, 'error': 'ID no proporcionado'}), 400
            
            # Buscar y eliminar el elemento
            download_queue_storage = [item for item in download_queue_storage if item['id'] != item_id]
            save_download_state()
            
            return jsonify({'success': True, 'message': 'Elemento eliminado de la cola'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Método no permitido'}), 405

def process_download_queue():
    """Procesa la cola de descargas automáticamente"""
    global download_queue_storage, queue_running
    
    while queue_running and download_queue_storage:
        try:
            # Verificar límite de descargas concurrentes
            active_downloads = sum(1 for d in multi_progress.values() if d['status'] == 'downloading')
            
            if active_downloads >= MAX_CONCURRENT_DOWNLOADS:
                time.sleep(5)  # Esperar 5 segundos antes de verificar de nuevo
                continue
            
            # Buscar el siguiente elemento pendiente
            next_item = None
            for item in download_queue_storage:
                if item['status'] == 'pending':
                    next_item = item
                    break
            
            if not next_item:
                time.sleep(2)  # No hay elementos pendientes
                continue
            
            # Marcar como procesando
            next_item['status'] = 'processing'
            save_download_state()
            
            # Simular llamada POST para iniciar descarga
            params = {
                'm3u8_url': next_item['url'],
                'output_name': next_item['name'],
                'quality': next_item.get('quality', DEFAULT_QUALITY)
            }
            
            with app.test_request_context('/descargar', method='POST', data=params):
                try:
                    result = descargar()
                    # Verificar si la respuesta indica éxito (código 202)
                    success = False
                    if isinstance(result, tuple) and len(result) == 2:
                        response, status_code = result
                        success = (status_code == 202)
                    
                    if success:
                        # Descarga iniciada correctamente
                        next_item['status'] = 'started'
                        # Remover de la cola
                        download_queue_storage = [item for item in download_queue_storage if item['id'] != next_item['id']]
                    else:
                        # Error al iniciar descarga
                        next_item['status'] = 'error'
                        next_item['error'] = 'Error al iniciar descarga'
                        
                except Exception as e:
                    next_item['status'] = 'error'
                    next_item['error'] = str(e)
                
            save_download_state()
            time.sleep(1)  # Pausa breve antes del siguiente elemento
            
        except Exception as e:
            print(f"Error procesando cola: {e}")
            time.sleep(5)
    
    queue_running = False
    save_download_state()

@app.route('/api/metadata', methods=['POST'])
def get_m3u8_metadata():
    """Obtiene metadatos de una URL M3U8 para sugerir nombre y mostrar información"""
    import requests  # Importar aquí para manejar timeout específicamente
    
    try:
        # Verificar que se reciban datos JSON válidos
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type debe ser application/json'}), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({'success': False, 'error': 'No se recibieron datos JSON válidos'}), 400
        
        m3u8_url = data.get('url', '').strip() if isinstance(data, dict) else ''
        
        if not m3u8_url:
            return jsonify({'success': False, 'error': 'URL no proporcionada en los datos JSON'}), 400
        
        if not is_valid_m3u8_url(m3u8_url):
            return jsonify({'success': False, 'error': f'URL M3U8 no válida: {m3u8_url}'}), 400
        
        print(f"Procesando metadatos para: {m3u8_url}")
        
        try:
            metadata = extract_m3u8_metadata(m3u8_url)
            suggested_filename = metadata['suggested_name'] or suggest_filename_from_m3u8(m3u8_url)
            
            print(f"Metadatos extraídos exitosamente. Nombre sugerido: {suggested_filename}")
            
            return jsonify({
                'success': True,
                'metadata': metadata,
                'suggested_filename': suggested_filename
            })
            
        except requests.Timeout:
            # Fallback para timeouts
            print(f"Timeout al acceder a {m3u8_url}, usando fallback")
            fallback_name = suggest_filename_from_url_only(m3u8_url)
            return jsonify({
                'success': True,
                'metadata': {'suggested_name': fallback_name, 'video_info': {'source': 'fallback'}},
                'suggested_filename': fallback_name,
                'warning': 'No se pudieron obtener metadatos completos (timeout), usando nombre básico'
            })
            
        except Exception as metadata_error:
            print(f"Error extrayendo metadatos de {m3u8_url}: {metadata_error}")
            # Fallback para otros errores
            fallback_name = suggest_filename_from_url_only(m3u8_url)
            return jsonify({
                'success': True,
                'metadata': {'suggested_name': fallback_name, 'video_info': {'source': 'fallback'}},
                'suggested_filename': fallback_name,
                'warning': f'No se pudieron obtener metadatos completos: {str(metadata_error)}'
            })
        
    except Exception as e:
        print(f"Error en /api/metadata: {str(e)}")
        return jsonify({'success': False, 'error': f'Error interno del servidor: {str(e)}'}), 500

@app.route('/api/active_downloads', methods=['GET'])
def get_active_downloads():
    """Obtiene todas las descargas activas para cargar al refrescar"""
    try:
        return jsonify({
            'success': True,
            'downloads': multi_progress
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/historial', methods=['GET'])
def get_historial():
    """Obtiene el historial de descargas actualizado"""
    try:
        import glob
        import os
        from datetime import datetime
        
        # Obtener todos los archivos MP4 del directorio static
        archivos = []
        static_dir = 'static'
        
        if os.path.exists(static_dir):
            for archivo in glob.glob(os.path.join(static_dir, '*.mp4')):
                nombre_archivo = os.path.basename(archivo)
                try:
                    file_stats = os.stat(archivo)
                    fecha_modificacion = datetime.fromtimestamp(file_stats.st_mtime)
                    
                    # Buscar URL asociada PRIMERO en metadata (.meta file)
                    url_asociada = None
                    fecha_descarga = None
                    
                    try:
                        metadata = load_video_metadata(nombre_archivo)
                        if metadata:
                            url_asociada = metadata.get('url')
                            fecha_descarga = metadata.get('download_date')
                            print(f"📋 Metadata cargada para {nombre_archivo}: URL={url_asociada}")
                        else:
                            print(f"⚠️ No se pudo cargar metadata para {nombre_archivo}")
                    except Exception as meta_error:
                        print(f"❌ Error cargando metadata para {nombre_archivo}: {meta_error}")
                    
                    # Si no se encontró en metadata, buscar en descargas activas como fallback
                    if not url_asociada:
                        for download_id, progress in multi_progress.items():
                            if progress.get('output_file') == nombre_archivo:
                                url_asociada = progress.get('url')
                                print(f"📥 URL encontrada en multi_progress para {nombre_archivo}: {url_asociada}")
                                break
                    
                    # Usar fecha de descarga de metadata si está disponible, sino fecha de modificación
                    fecha_para_mostrar = fecha_modificacion.strftime('%d/%m/%Y %H:%M')
                    timestamp_para_ordenar = int(file_stats.st_mtime)
                    
                    if fecha_descarga:
                        try:
                            # Parsear fecha de metadata (formato ISO)
                            dt_descarga = datetime.fromisoformat(fecha_descarga.replace('Z', '+00:00').replace('+00:00', ''))
                            fecha_para_mostrar = dt_descarga.strftime('%d/%m/%Y %H:%M')
                            timestamp_para_ordenar = int(dt_descarga.timestamp())
                            print(f"📅 Usando fecha de metadata para {nombre_archivo}: {fecha_para_mostrar}")
                        except Exception as date_error:
                            print(f"⚠️ Error parseando fecha de metadata: {date_error}")
                    
                    archivos.append({
                        'archivo': nombre_archivo,
                        'tamaño': format_file_size(file_stats.st_size),
                        'tamaño_bytes': file_stats.st_size,
                        'fecha': fecha_para_mostrar,
                        'fecha_timestamp': timestamp_para_ordenar,
                        'url': url_asociada
                    })
                    
                    print(f"✅ Procesado {nombre_archivo} - URL: {url_asociada}")
                    
                except Exception as e:
                    print(f"❌ Error procesando archivo {archivo}: {e}")
        
        # Ordenar por fecha de modificación (más recientes primero)
        archivos.sort(key=lambda x: x['fecha_timestamp'], reverse=True)
        
        print(f"📊 Historial generado: {len(archivos)} archivos")
        for archivo in archivos:
            print(f"  📄 {archivo['archivo']} - URL: {archivo['url']}")
        
        return jsonify({
            'success': True,
            'historial': archivos
        })
    except Exception as e:
        error_msg = f"Error generando historial: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Endpoint para obtener datos analíticos"""
    try:
        static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
        
        # Analizar archivos por tamaño y fecha
        files_by_date = {}
        size_distribution = {'small': 0, 'medium': 0, 'large': 0}
        
        if os.path.exists(static_dir):
            for f in glob.glob(os.path.join(static_dir, '*.mp4')):
                file_stats = os.stat(f)
                date_key = format_modification_time(file_stats.st_mtime)[:10]  # Solo fecha
                
                if date_key not in files_by_date:
                    files_by_date[date_key] = 0
                files_by_date[date_key] += 1
                
                # Categorizar por tamaño
                size_mb = file_stats.st_size / (1024 * 1024)
                if size_mb < 50:
                    size_distribution['small'] += 1
                elif size_mb < 200:
                    size_distribution['medium'] += 1
                else:
                    size_distribution['large'] += 1
        
        return jsonify({
            'success': True,
            'analytics': {
                'files_by_date': files_by_date,
                'size_distribution': size_distribution,
                'total_active_downloads': len(multi_progress),
                'success_rate': calculate_success_rate()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_success_rate():
    """Calcula la tasa de éxito de las descargas"""
    if not multi_progress:
        return 100
    
    completed = sum(1 for d in multi_progress.values() if d['status'] == 'done')
    total = len(multi_progress)
    
    return round((completed / total) * 100, 1) if total > 0 else 100

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
