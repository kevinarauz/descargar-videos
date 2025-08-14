# CLAUDE.md

Este archivo proporciona guía a Claude Code (claude.ai/code) al trabajar con código en este repositorio.

## Resumen del Proyecto

Este es un descargador de videos M3U8 de alto rendimiento con una interfaz web moderna. La aplicación proporciona una solución optimizada para descargar videos HLS (HTTP Live Streaming) con características como descarga concurrente, seguimiento de progreso en tiempo real, reanudación de descargas y múltiples descargas simultáneas.

## Arquitectura

### Componentes Principales

- **Servidor Web Flask** (`app.py`): Aplicación principal que proporciona endpoints de API REST y sirve la interfaz web
- **Clase M3U8Downloader** (`test.py`): Motor de descarga principal con procesamiento paralelo optimizado (hasta 1000 workers)
- **Interfaz Web** (`index.html`): UI moderna y responsiva con monitoreo de progreso en tiempo real
- **Gestión de Estado**: Estado persistente de descargas usando `download_state.json` para recuperación entre reinicios

### Características Técnicas Clave

- **Descargas de Alto Rendimiento**: Usa ThreadPoolExecutor con workers configurables (predeterminado 30, puede llegar hasta 1000)
- **Sesión HTTP Optimizada**: HTTPAdapter personalizado con pool de conexiones y reintentos automáticos
- **Procesamiento de Segmentos**: Descarga segmentos de playlist M3U8 en paralelo, luego los une usando FFmpeg
- **Capacidad de Reanudación**: Puede reanudar descargas interrumpidas detectando segmentos existentes
- **Sistema de Cola**: Gestiona múltiples descargas simultáneas con límites configurables (predeterminado 5 concurrentes)

## Comandos de Desarrollo

### Iniciar la Aplicación
```bash
python app.py
```
La aplicación se ejecuta en `http://localhost:5000`

### Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Dependencias Externas Requeridas
- **FFmpeg**: Debe estar instalado y disponible en PATH para la unión de segmentos de video
  - Windows: Descargar desde https://ffmpeg.org/download.html
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`

### Verificar Instalación de FFmpeg
```bash
ffmpeg -version
```

## Estructura de Archivos Clave

```
├── app.py                    # Aplicación Flask principal con endpoints API
├── test.py                   # Clase M3U8Downloader (motor de descarga principal)
├── index.html                # Interfaz web con UI en tiempo real
├── requirements.txt          # Dependencias de Python
├── download_state.json       # Estado persistente de descargas (auto-generado)
├── static/                   # Almacenamiento de archivos MP4 descargados
└── temp_segments/           # Almacenamiento temporal de segmentos durante descargas
```

## Detalles Técnicos Importantes

### Gestión de Estado de Descargas
La aplicación mantiene estado persistente en `download_state.json` con:
- Seguimiento de progreso de descargas activas
- Gestión de cola de descargas
- Información de capacidad de reanudación
- Estados de error y datos de recuperación

Ver `DOWNLOAD_STATE_STRUCTURE.md` para esquema detallado del estado.

### Optimizaciones de Rendimiento
- **1000 workers concurrentes** para máximo paralelismo
- **Chunks de 8MB** para transferencias de alta velocidad
- **Pool de conexiones** con sesiones HTTP persistentes
- **Headers de compresión Brotli** para reducir ancho de banda
- **Lógica de reintentos inteligente** para segmentos fallidos

### Consideraciones de Seguridad
- Validación de entrada para URLs M3U8 y nombres de archivo
- Protección contra path traversal para operaciones de archivo
- Sanitización segura de nombres de archivo
- Manejo seguro de archivos temporales

## Endpoints de API

Rutas Flask clave en `app.py`:
- `GET /`: Sirve la interfaz web principal
- `POST /download`: Inicia descarga M3U8
- `GET /progress`: Retorna progreso de descarga en tiempo real
- `POST /cancel/<download_id>`: Cancela descarga activa
- `GET /files`: Lista archivos descargados
- `DELETE /files/<filename>`: Elimina archivo descargado

## Problemas Comunes

### FFmpeg No Encontrado
Asegúrate de que FFmpeg esté instalado y accesible vía PATH. La aplicación requiere FFmpeg para unir segmentos de video.

### Alto Uso de CPU/Memoria
La aplicación está diseñada para descargas de alto rendimiento con muchos workers concurrentes. Ajusta el parámetro `max_workers` en M3U8Downloader si es necesario.

### Videos Cifrados
Videos con `#EXT-X-KEY` (DRM/cifrado) no son soportados y mostrarán mensajes de error apropiados.