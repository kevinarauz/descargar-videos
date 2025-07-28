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

# Configuración
MAX_CONCURRENT_DOWNLOADS = 5
STATIC_DIR = 'static'
TEMP_DIR = 'temp_segments'

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
      <h3>Historial de descargas</h3>
      {% if stats and stats.total > 0 %}
        <div class="download-stats">
          <small>
            📊 Activas: <span class="status-downloading">●</span> {{stats.downloading}} | 
            ✅ {{stats.completed}} | ❌ {{stats.errors}} | 🚫 {{stats.cancelled}}
          </small>
        </div>
        <hr style="margin: 0.5rem 0;">
      {% endif %}
      {% if historial and historial|length > 0 %}
        <ul>
        {% for item in historial %}
          <li class="d-flex justify-content-between align-items-center mb-2">
            <div class="flex-grow-1 me-2">
              <a href="/static/{{item.archivo}}" download class="text-truncate d-block">{{item.archivo}}</a>
              <div class="download-stats">
                📦 {{item.tamaño}} • 📅 {{item.fecha}}
                {% if item.url %}
                <br><small class="url-metadata">
                  🔗 <span class="text-break" style="font-size: 0.75em;">{{item.url}}</span>
                </small>
                {% endif %}
              </div>
            </div>
            <div class="d-flex flex-column">
              {% if item.url %}
              <button class="btn btn-outline-info btn-sm mb-1" data-url="{{item.url|e}}" onclick="copiarUrlFromData(this)" title="Copiar URL al portapapeles">
                📋
              </button>
              <button class="btn btn-outline-success btn-sm mb-1" data-url="{{item.url|e}}" onclick="reproducirUrlFromData(this)" title="Reproducir video">
                ▶️
              </button>
              {% endif %}
              <button class="btn btn-outline-danger btn-sm" onclick="eliminarArchivo('{{item.archivo}}')" title="Eliminar archivo">
                🗑️
              </button>
            </div>
          </li>
        {% endfor %}
        </ul>
      {% else %}
        <span style="color:#ccc">No hay descargas aún.</span>
      {% endif %}
      <hr>
      <h3>Descargas activas</h3>
      <div id="descargas-activas"></div>
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
            <button type="submit" class="btn btn-success d-flex align-items-center gap-2">
              <span>⬇️</span> Descargar MP4
            </button>
          </div>
        </form>
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
          <div class="small opacity-75">Versión 1.0.0 - Interfaz moderna con principios UI/UX</div>
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
            // Obtener la URL del formulario para pasarla a la descarga activa
            let url = document.getElementById('m3u8-url').value.trim();
            mostrarDescargaActiva(data.download_id, url);
        }
    });
});
function mostrarDescargaActiva(download_id, url) {
    let div = document.getElementById('descargas-activas');
    let barra = document.createElement('div');
    barra.id = 'descarga-' + download_id;
    barra.className = 'descarga-item';
    barra.innerHTML = `
        <div>
            <span class="status-indicator status-downloading"></span>
            <strong id='archivo-${download_id}'>Preparando descarga...</strong>
        </div>
        <div class="download-stats" id="stats-${download_id}">
            Inicializando...
        </div>
        <div class='mt-2 url-display small' id="url-${download_id}">
            <strong>🔗 URL:</strong> <span class="text-break">${url || 'N/A'}</span>
        </div>
        <div>Progreso: <span id='progreso-${download_id}'>0%</span></div>
        <div class='progress mb-2'>
            <div class='progress-bar' id='bar-${download_id}' role='progressbar' style='width:0%'></div>
        </div>
        <div>
            <button class='btn btn-danger btn-sm' id='cancel-btn-${download_id}' onclick='cancelarDescarga("${download_id}")'>Cancelar</button>
        </div>`;
    
    div.appendChild(barra);
    
    // Agregar botón de copiar URL si existe
    if (url) {
        let urlDiv = document.getElementById(`url-${download_id}`);
        let copyBtn = document.createElement('button');
        copyBtn.className = 'btn btn-outline-info btn-sm ms-2';
        copyBtn.innerHTML = '📋';
        copyBtn.title = 'Copiar URL';
        copyBtn.onclick = function() { copiarUrl(url); };
        urlDiv.appendChild(copyBtn);
    }
    
    actualizarProgreso(download_id);
}
function actualizarProgreso(download_id) {
    fetch('/progreso/' + download_id).then(r => r.json()).then(data => {
        let bar = document.getElementById('bar-' + download_id);
        let prog = document.getElementById('progreso-' + download_id);
        let archivo = document.getElementById('archivo-' + download_id);
        let cancelBtn = document.getElementById('cancel-btn-' + download_id);
        let descargaDiv = document.getElementById('descarga-' + download_id);
        let stats = document.getElementById('stats-' + download_id);
        
        if (data.output_file && archivo) {
            archivo.innerHTML = `<span class="status-indicator status-${data.status}"></span>📥 ${data.output_file}`;
        }
        
        if (stats && data.total > 0) {
            let segmentos = `${data.current || 0}/${data.total} segmentos`;
            if (data.status === 'downloading') {
                let velocidad = data.current && data.start_time ? 
                    ((data.current / (Date.now()/1000 - data.start_time)) * 60).toFixed(1) : '0';
                stats.innerText = `${segmentos} • ~${velocidad} seg/min`;
            } else {
                stats.innerText = segmentos;
            }
        }
        
        if (data.status === 'downloading') {
            bar.style.width = data.porcentaje + '%';
            prog.innerText = data.porcentaje + '%';
            descargaDiv.className = 'descarga-item';
            setTimeout(function() { actualizarProgreso(download_id); }, 1000);
        } else if (data.status === 'done') {
            bar.style.width = '100%';
            prog.innerText = '100%';
            if (archivo) archivo.innerHTML = `<span class="status-indicator status-done"></span>✅ ${data.output_file}`;
            if (cancelBtn) cancelBtn.style.display = 'none';
            if (descargaDiv) descargaDiv.className += ' descarga-done';
            if (stats) {
                let duracion = data.end_time && data.start_time ? 
                    Math.round(data.end_time - data.start_time) : 0;
                stats.innerText = `Completado en ${duracion}s`;
            }
            document.getElementById('descarga-' + download_id).innerHTML += `
                <div class='mt-2'>
                    <a href='/static/${data.output_file}' download class='btn btn-primary btn-sm me-2'>Descargar MP4</a>
                    <button class='btn btn-outline-secondary btn-sm' onclick='eliminarDescargaActiva("${download_id}")' title='Eliminar de la lista'>
                        🗑️ Quitar
                    </button>
                </div>`;
            // Actualizar el historial automáticamente
            setTimeout(function() { 
                location.reload(); 
            }, 2000);
        } else if (data.status === 'error') {
            if (archivo) archivo.innerHTML = `<span class="status-indicator status-error"></span>❌ ${data.output_file || 'Error'}`;
            if (cancelBtn) cancelBtn.style.display = 'none';
            if (descargaDiv) descargaDiv.className += ' descarga-error';
            if (stats) stats.innerText = 'Error en la descarga';
            document.getElementById('descarga-' + download_id).innerHTML += `
                <div class='mt-2 text-danger'>${data.error}</div>
                <div class='mt-2 url-display small'>
                    <strong>🔗 URL:</strong> <span class="text-break">${data.url || 'N/A'}</span>
                </div>
                <div class='mt-2'>
                    <button class='btn btn-warning btn-sm me-2' onclick='reintentarDescarga("${download_id}")' title='Reintentar descarga'>
                        🔄 Reintentar
                    </button>
                    <button class='btn btn-success btn-sm me-2' onclick='reproducirUrlActiva("${download_id}")' title='Reproducir video'>
                        ▶️ Reproducir
                    </button>
                    <button class='btn btn-outline-secondary btn-sm' onclick='eliminarDescargaActiva("${download_id}")' title='Eliminar de la lista'>
                        🗑️ Quitar
                    </button>
                </div>`;
        } else if (data.status === 'cancelled') {
            if (archivo) archivo.innerHTML = `<span class="status-indicator status-cancelled"></span>🚫 Descarga cancelada`;
            if (cancelBtn) cancelBtn.style.display = 'none';
            if (descargaDiv) descargaDiv.className += ' descarga-cancelled';
            if (stats) stats.innerText = 'Cancelado por el usuario';
            document.getElementById('descarga-' + download_id).innerHTML += `
                <div class='mt-2 text-warning'>Descarga cancelada por el usuario</div>
                <div class='mt-2 url-display small'>
                    <strong>🔗 URL:</strong> <span class="text-break">${data.url || 'N/A'}</span>
                </div>
                <div class='mt-2'>
                    <button class='btn btn-warning btn-sm me-2' onclick='reintentarDescarga("${download_id}")' title='Reintentar descarga'>
                        🔄 Reintentar
                    </button>
                    <button class='btn btn-success btn-sm me-2' onclick='reproducirUrlActiva("${download_id}")' title='Reproducir video'>
                        ▶️ Reproducir
                    </button>
                    <button class='btn btn-outline-secondary btn-sm' onclick='eliminarDescargaActiva("${download_id}")' title='Eliminar de la lista'>
                        🗑️ Quitar
                    </button>
                </div>`;
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
                if (archivo) archivo.innerText = `🚫 Cancelando...`;
            }
        });
    }
}
function eliminarArchivo(filename) {
    if (confirm(`¿Estás seguro de que quieres eliminar el archivo "${filename}"?\n\nEsta acción no se puede deshacer.`)) {
        fetch('/eliminar/' + encodeURIComponent(filename), {
            method: 'DELETE'
        }).then(r => r.json()).then(data => {
            if (data.success) {
                // Recargar la página para actualizar el historial
                location.reload();
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
        fetch('/eliminar_descarga/' + download_id, {
            method: 'DELETE'
        }).then(r => r.json()).then(data => {
            if (data.success) {
                // Remover el elemento del DOM
                let elemento = document.getElementById('descarga-' + download_id);
                if (elemento) {
                    elemento.remove();
                }
                // Actualizar estadísticas si es necesario
                setTimeout(function() {
                    location.reload();
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
    // Obtener los datos de la descarga fallida
    fetch('/progreso/' + download_id).then(r => r.json()).then(data => {
        if (data.url && data.output_file) {
            if (confirm(`¿Reintentar la descarga de "${data.output_file}"?`)) {
                // Rellenar el formulario con los datos de la descarga fallida
                document.getElementById('m3u8-url').value = data.url;
                document.getElementById('output-name').value = data.output_file.replace('.mp4', '');
                
                // Eliminar la descarga fallida de la lista
                fetch('/eliminar_descarga/' + download_id, {
                    method: 'DELETE'
                }).then(() => {
                    // Remover el elemento del DOM inmediatamente
                    let elemento = document.getElementById('descarga-' + download_id);
                    if (elemento) {
                        elemento.remove();
                    }
                    
                    // Iniciar nueva descarga automáticamente
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
    // Decodificar la URL si está codificada
    let urlToCopy = decodeURIComponent(url);
    
    if (navigator.clipboard && window.isSecureContext) {
        // Usar la API moderna del portapapeles
        navigator.clipboard.writeText(urlToCopy).then(function() {
            // Mostrar confirmación temporal
            let button = event.target;
            let originalText = button.innerHTML;
            button.innerHTML = '✅';
            button.disabled = true;
            setTimeout(function() {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 1500);
        }).catch(function(err) {
            // Fallback si falla la API moderna
            copiarUrlFallback(urlToCopy);
        });
    } else {
        // Fallback para navegadores más antiguos
        copiarUrlFallback(urlToCopy);
    }
}
function copiarUrlFromData(button) {
    // Obtener URL del atributo data
    let url = button.getAttribute('data-url');
    if (!url) {
        alert('No se encontró la URL para copiar.');
        return;
    }
    
    if (navigator.clipboard && window.isSecureContext) {
        // Usar la API moderna del portapapeles
        navigator.clipboard.writeText(url).then(function() {
            // Mostrar confirmación temporal
            let originalText = button.innerHTML;
            button.innerHTML = '✅';
            button.disabled = true;
            setTimeout(function() {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 1500);
        }).catch(function(err) {
            // Fallback si falla la API moderna
            copiarUrlFallback(url);
        });
    } else {
        // Fallback para navegadores más antiguos
        copiarUrlFallback(url);
    }
}
function reproducirUrl(url) {
    // Decodificar la URL y ponerla en el campo de entrada
    let urlToPlay = decodeURIComponent(url);
    document.getElementById('m3u8-url').value = urlToPlay;
    
    // Reproducir automáticamente
    playM3U8();
    
    // Mostrar confirmación visual en el botón
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
    // Obtener URL del atributo data
    let url = button.getAttribute('data-url');
    if (!url) {
        alert('No se encontró la URL para reproducir.');
        return;
    }
    
    // Poner la URL en el campo de entrada
    document.getElementById('m3u8-url').value = url;
    
    // Reproducir automáticamente
    playM3U8();
    
    // Mostrar confirmación visual en el botón
    let originalText = button.innerHTML;
    button.innerHTML = '🎬';
    button.disabled = true;
    setTimeout(function() {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 2000);
}
function reproducirUrlActiva(download_id) {
    // Obtener los datos de la descarga para acceder a la URL
    fetch('/progreso/' + download_id).then(r => r.json()).then(data => {
        if (data.url) {
            // Poner la URL en el campo de entrada
            document.getElementById('m3u8-url').value = data.url;
            
            // Reproducir automáticamente
            playM3U8();
            
            // Mostrar confirmación visual en el botón
            let button = event.target;
            let originalText = button.innerHTML;
            button.innerHTML = '🎬 Reproduciendo';
            button.disabled = true;
            setTimeout(function() {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 3000);
        } else {
            alert('No se pudo obtener la URL para reproducir.');
        }
    }).catch(error => {
        alert('Error al obtener la URL: ' + error.message);
    });
}
function copiarUrlFallback(url) {
    // Decodificar la URL si está codificada
    let urlToCopy = typeof url === 'string' ? decodeURIComponent(url) : url;
    
    // Crear un elemento temporal para copiar
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
            
            archivo_info = {
                'archivo': filename,
                'tamaño': format_file_size(os.path.getsize(f)),
                'fecha': format_modification_time(os.path.getmtime(f)),
                'url': metadata['url'] if metadata and 'url' in metadata else None
            }
            archivos.append(archivo_info)
        # Ordenar por fecha de modificación (más reciente primero)
        archivos.sort(key=lambda x: os.path.getmtime(os.path.join(static_dir, x['archivo'])), reverse=True)
    
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
    """Limpia el nombre del archivo de caracteres no seguros"""
    return re.sub(r'[^\w\-. ]', '', filename).strip()

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
    
    # Validaciones de entrada
    if not m3u8_url:
        return jsonify({'error': 'URL M3U8 no proporcionada'}), 400
    
    if not is_valid_m3u8_url(m3u8_url):
        return jsonify({'error': 'URL M3U8 no válida'}), 400
    
    # Procesar nombre del archivo
    if output_name:
        output_name = sanitize_filename(output_name)
        if not output_name.lower().endswith('.mp4'):
            output_name += '.mp4'
        output_file = output_name
    else:
        output_file = f'video_{uuid.uuid4().hex[:8]}.mp4'
    
    # Verificar si el archivo ya existe
    static_dir = os.path.join(os.path.dirname(__file__), STATIC_DIR)
    if os.path.exists(os.path.join(static_dir, output_file)):
        base_name = output_file[:-4]  # Sin .mp4
        counter = 1
        while os.path.exists(os.path.join(static_dir, f"{base_name}_{counter}.mp4")):
            counter += 1
        output_file = f"{base_name}_{counter}.mp4"
    
    # Crear ID único para la descarga
    download_id = str(uuid.uuid4())
    multi_progress[download_id] = {
        'total': 0,
        'current': 0,
        'status': 'downloading',
        'error': '',
        'porcentaje': 0,
        'output_file': output_file,
        'url': m3u8_url,
        'start_time': time.time()
    }
    
    def run_download():
        # Crear directorio temporal único para esta descarga (fuera del try)
        temp_dir = os.path.join(os.path.dirname(__file__), TEMP_DIR, download_id)
        
        try:
            # Verificar si ya fue cancelado antes de empezar
            if download_id in cancelled_downloads:
                multi_progress[download_id]['status'] = 'cancelled'
                return
                
            # Crear el directorio temporal
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            original_dir = os.getcwd()
            
            # Descarga de segmentos con directorio específico
            downloader = M3U8Downloader(m3u8_url=m3u8_url, output_filename=output_file, max_workers=20, temp_dir=temp_dir)
            segment_urls = downloader._get_segment_urls()
            multi_progress[download_id]['total'] = len(segment_urls)
            
            for i, url in enumerate(segment_urls):
                # Verificar cancelación en cada iteración
                if download_id in cancelled_downloads:
                    multi_progress[download_id]['status'] = 'cancelled'
                    multi_progress[download_id]['error'] = 'Descarga cancelada por el usuario'
                    return
                    
                try:
                    downloader._download_segment(url, i)
                    seg_path = os.path.join(temp_dir, f'segment_{i:05d}.ts')
                    if not os.path.exists(seg_path):
                        raise FileNotFoundError(f"No se encontró el archivo {seg_path} tras la descarga.")
                except Exception as err:
                    multi_progress[download_id]['error'] = f"Error al descargar el segmento {i+1}: {err}"
                    multi_progress[download_id]['status'] = 'error'
                    break
                    
                porcentaje = int(((i + 1) / len(segment_urls)) * 100) if len(segment_urls) > 0 else 0
                multi_progress[download_id]['current'] = i + 1
                multi_progress[download_id]['porcentaje'] = porcentaje
                
            # Verificar cancelación antes de la fusión
            if download_id in cancelled_downloads:
                multi_progress[download_id]['status'] = 'cancelled'
                multi_progress[download_id]['error'] = 'Descarga cancelada por el usuario'
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
                    
                    # Guardar metadatos del video (URL y fecha de descarga)
                    try:
                        save_video_metadata(output_file, m3u8_url)
                    except Exception as meta_error:
                        print(f"Error al guardar metadatos: {meta_error}")
                else:
                    multi_progress[download_id]['status'] = 'error'
                    multi_progress[download_id]['error'] = 'No se pudo descargar el video o el archivo está vacío.'
                    
        except Exception as e:
            multi_progress[download_id]['status'] = 'error'
            multi_progress[download_id]['error'] = str(e)
        finally:
            # Limpiar el directorio temporal específico de esta descarga
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Error al limpiar directorio temporal {temp_dir}: {cleanup_error}")
            
            # Limpiar el ID de cancelación cuando termine la descarga
            cancelled_downloads.discard(download_id)
    
    thread = threading.Thread(target=run_download)
    thread.start()
    return jsonify({'download_id': download_id}), 202

@app.route('/progreso/<download_id>', methods=['GET'])
def progreso(download_id):
    if download_id not in multi_progress:
        return jsonify({'status': 'error', 'error': 'ID de descarga no encontrado.'}), 404
    return jsonify(multi_progress[download_id]), 200

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
    try:
        if download_id not in multi_progress:
            return jsonify({'success': False, 'error': 'ID de descarga no encontrado.'}), 404
        
        status = multi_progress[download_id]['status']
        
        # Solo permitir eliminar descargas que no están activamente descargando
        if status == 'downloading':
            return jsonify({'success': False, 'error': 'No se puede eliminar una descarga en progreso. Cancélala primero.'}), 400
        
        # Eliminar la descarga del progreso
        del multi_progress[download_id]
        cancelled_downloads.discard(download_id)
        
        return jsonify({'success': True, 'message': 'Descarga eliminada de la lista.'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error al eliminar la descarga: {str(e)}'}), 500

@app.route('/static/<path:filename>', methods=['GET'])
def serve_static(filename):
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_file(os.path.join(static_dir, filename))

@app.route('/favicon.ico')
def favicon():
    # Devolver un favicon básico o un 204 No Content
    from flask import Response
    return Response(status=204)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
