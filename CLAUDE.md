# CLAUDE.md

Este archivo proporciona orientación a Claude Code (claude.ai/code) al trabajar con el código en este repositorio.

## Comandos de Desarrollo

### Ejecutar la Aplicación
```bash
python app.py
```
La aplicación Flask se iniciará en `http://localhost:5000`

### Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Requisito de FFmpeg
Este proyecto requiere que FFmpeg esté instalado y disponible en el PATH del sistema para la fusión de segmentos de video:
- **Windows**: Descargar desde [FFmpeg.org](https://ffmpeg.org/download.html) y agregar al PATH
- **Linux**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`

Verificar instalación: `ffmpeg -version`

## Descripción de la Arquitectura

### Componentes Principales

**Aplicación Web Flask (`app.py`)**
- Servidor web principal que sirve tanto la UI como los endpoints de API
- Maneja múltiples descargas concurrentes con gestión de hilos
- Implementa persistencia del estado de descarga vía `download_state.json`
- Gestiona operaciones de archivos en el directorio `static/` para videos descargados

**Clase M3U8 Downloader (`m3u8_downloader.py`)**
- Lógica principal de descarga para playlists M3U8
- Soporta descarga paralela de segmentos de alto rendimiento (workers configurables)
- Implementa lógica de reintentos y pooling de conexiones para confiabilidad
- Maneja playlists maestras y selección de calidad automáticamente
- Usa FFmpeg para la fusión final de video

**Interfaz Web (`index.html` incrustado en `app.py`)**
- UI responsiva moderna con seguimiento de progreso en tiempo real
- Soporta múltiples descargas simultáneas con barras de progreso visuales
- Reproductor de video M3U8 integrado usando hls.js
- Historial de descargas con gestión completa de archivos
- Selector de modo de velocidad Normal/Turbo en la interfaz
- Sistema de notificaciones mejoradas con soporte multilinea
- Funcionalidades de archivo: renombrar, eliminar, expandir/contraer

### Características Principales

**Descargas de Alto Rendimiento**
- Hasta 1000 workers simultáneos para máximo throughput
- Sesión HTTP optimizada con pooling de conexiones
- Tamaños de chunk de 8MB para transferencias de alta velocidad
- Headers de compresión (Brotli/gzip) para eficiencia de ancho de banda

**Gestión de Descargas**
- Capacidad de reanudar descargas interrumpidas
- Sistema de cola de descargas con límites de concurrencia configurables
- Seguimiento de progreso en tiempo real con cálculos de velocidad y ETA
- Persistencia de estado a través de reinicios de aplicación

**Organización de Archivos**
- `static/` - Descargas MP4 finales (excluido de git)
  - `static/YYYY-MM/` - Organización automática por fecha cuando `AUTO_ORGANIZE_BY_DATE = True`
  - `static/archivo.mp4.meta` - Archivos de metadatos JSON con URL original y fecha de descarga
- `temp_segments/` - Segmentos TS temporales durante descarga (excluido de git)
- `download_state.json` - Estado persistente de descarga (excluido de git)

### Gestión de Estado

La aplicación mantiene el estado de descarga en `download_state.json` con la siguiente estructura:
- `multi_progress`: Descargas activas/completadas con información de progreso
- `download_queue`: Descargas en cola esperando para iniciar
- `queue_running`: Estado del procesador de cola

Las descargas interrumpidas por reinicio de aplicación se marcan automáticamente como "pausadas" y pueden reanudarse.

### Constantes de Configuración

Configuración principal en la parte superior de `app.py`:
```python
# === CONFIGURACIÓN FÁCIL ===
MAX_WORKERS_NORMAL = 30          # Workers modo Normal
MAX_WORKERS_TURBO = 100         # Workers modo Turbo
AUTO_ORGANIZE_BY_DATE = True    # Organizar por fecha automáticamente
ENABLE_DETAILED_LOGGING = True  # Logging detallado con emojis
MAX_CONCURRENT_DOWNLOADS = 5    # Máximo de descargas simultáneas
```

**Configuraciones disponibles:**
- Modo de velocidad: Normal (30 workers) vs Turbo (100 workers)
- Organización automática por fecha en carpetas `static/YYYY-MM/`
- Logging mejorado con timestamps y emojis
- Sistema de metadatos JSON para preservar URLs originales

### Consideraciones de Seguridad

- Validación de entrada para URLs M3U8 y nombres de archivo
- Protección contra path traversal para operaciones de archivo
- Sanitización segura de nombres de archivo
- Limpieza de archivos temporales en errores

### Endpoints de API

**Principales:**
- `GET /` - Interfaz principal
- `POST /download` - Iniciar nueva descarga
- `GET /progress/<download_id>` - Obtener progreso de descarga
- `POST /cancel/<download_id>` - Cancelar descarga activa

**Gestión de Archivos:**
- `GET /api/historial` - Obtener historial completo de descargas (busca recursivamente)
- `DELETE /eliminar/<filename>` - Eliminar archivo (busca en subdirectorios)
- `POST /renombrar/<filename>` - Renombrar archivo (mantiene metadatos)
- `GET /download_file/<filename>` - Descargar archivo al cliente

**Configuración:**
- `GET /api/speed_mode` - Obtener modo de velocidad actual
- `POST /api/speed_mode` - Cambiar modo de velocidad (Normal/Turbo)

### Manejo de Errores

- Reintentos automáticos para descargas de segmentos fallidas
- Degradación elegante cuando faltan segmentos
- Detección y reporte de errores de FFmpeg
- Manejo de timeouts de red con límites configurables

### Mejoras Implementadas (v2.0)

**Sistema de Metadatos:**
- Archivos `.meta` JSON almacenan URL original, fecha de descarga y ruta de archivo
- Función `find_video_metadata()` busca metadatos recursivamente
- Preservación de metadatos durante renombrado y eliminación

**Organización Automática por Fecha:**
- Videos se organizan en `static/YYYY-MM/` cuando `AUTO_ORGANIZE_BY_DATE = True`
- Función `get_organized_path()` calcula rutas automáticamente
- Sistema compatible con archivos existentes en raíz

**Selector de Velocidad:**
- Modo Normal (30 workers) vs Turbo (100+ workers)
- Toggle en interfaz para cambio dinámico
- API endpoints para configuración programática

**Logging Mejorado:**
- Timestamps y emojis descriptivos cuando `ENABLE_DETAILED_LOGGING = True`
- Funciones especializadas: `log_info()`, `log_download_start()`, `log_download_progress()`, `log_download_complete()`
- Rastreo detallado del proceso de descarga

**Gestión de Archivos Robusta:**
- Búsqueda recursiva en subdirectorios para todas las operaciones
- Historial unificado que encuentra archivos en cualquier ubicación
- Operaciones de archivo mantienen sincronización con metadatos

### Funciones Clave Agregadas

```python
# Búsqueda y metadatos
find_all_mp4_files()                    # Busca MP4s recursivamente
find_video_metadata(filename)           # Busca metadatos de archivo
save_video_metadata_with_path(path, url) # Guarda metadatos con ruta completa

# Organización
get_organized_path(filename)            # Calcula ruta organizada por fecha
get_current_workers()                   # Obtiene workers según modo actual

# Logging
log_info(message)                       # Log con timestamp y emoji
log_download_start(url, filename)       # Log inicio de descarga
log_download_complete(filename, stats)   # Log finalización con estadísticas
```

### Notas de Desarrollo

- No se requiere proceso de build - aplicación Flask pura en Python
- Usa plantillas HTML incrustadas en `app.py` por simplicidad
- Gestión de descargas thread-safe con bloqueo apropiado
- Logging comprensivo para debugging de problemas de descarga
- Sistema de metadatos backward-compatible con descargas existentes
- Configuración centralizada en la parte superior de `app.py` para fácil personalización