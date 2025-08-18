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
- Funcionalidades de archivo: renombrar, eliminar, copiar URL, reproducir

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
- `POST /analizar` - Analizar URL M3U8 para detectar encriptación/DRM antes de descargar

**Master Playlist y Calidad:**
- `POST /api/parse_master` - Analizar Master Playlist y extraer opciones de calidad
- `POST /api/metadata` - Obtener metadatos M3U8 y sugerir nombre de archivo

**DRM y Desencriptación:**
- `POST /api/drm/analyze` - Analizar contenido M3U8 para detectar DRM y claves de encriptación
- `POST /api/drm/decrypt` - Iniciar proceso de descifrado DRM (solo investigación académica)
- `GET /api/drm/status/<decrypt_id>` - Obtener estado en tiempo real del proceso de descifrado
- `GET /api/drm/check` - Verificar disponibilidad de módulos DRM

**Gestión de Archivos:**
- `GET /api/historial` - Obtener historial completo de descargas (busca recursivamente)
- `DELETE /eliminar/<filename>` - Eliminar archivo (busca en subdirectorios)
- `POST /renombrar/<filename>` - Renombrar archivo (mantiene metadatos)
- `GET /download_file/<filename>` - Descargar archivo al cliente

**Configuración:**
- `GET /api/speed_mode` - Obtener modo de velocidad actual
- `POST /api/speed_mode` - Cambiar modo de velocidad (Normal/Turbo)

**Logging y Debugging:**
- `POST /api/log_js_error` - Recibir y registrar errores JavaScript del frontend

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
- Sistema de logs específicos por descarga con archivos `.log`
- Captura y envío de errores JavaScript al servidor

**Gestión de Archivos Robusta:**
- Búsqueda recursiva en subdirectorios para todas las operaciones
- Historial unificado que encuentra archivos en cualquier ubicación
- Operaciones de archivo mantienen sincronización con metadatos

### Mejoras Implementadas (v3.0) - Master Playlist y Tiempo de Proceso

**Sistema de Master Playlist:**
- Detección automática de Master Playlists con múltiples calidades de video
- Selector de calidad visual con información detallada (resolución, bitrate)
- Conversión automática de URLs relativas a absolutas
- Función `parse_master_playlist()` para análisis de calidades disponibles
- Endpoint `/api/parse_master` para análisis dinámico de playlists

**Medición de Tiempo Mejorada:**
- Tiempo transcurrido y restante estimado durante descargas normales
- Velocidad de descarga en MB/s y segmentos/minuto  
- Tiempo total de descarga al completar con estadísticas detalladas
- Cálculos de ETA precisos basados en velocidad actual de procesamiento

**Progreso de Desencriptación DRM en Tiempo Real:**
- Seguimiento detallado del progreso de descifrado segmento por segmento
- Tiempo restante estimado durante desencriptación con cálculos dinámicos
- Separación clara entre fases: Descifrado → Unión → Completado
- Progreso visual de FFmpeg durante unión con estimación de tiempo restante
- Sistema de callbacks para reportar progreso en tiempo real

**GitIgnore Optimizado:**
- Exclusión de segmentos temporales (.ts) y directorios de trabajo DRM
- Inclusión selectiva de videos MP4 finales y archivos de metadatos
- Protección de archivos importantes mientras se ignoran temporales

### Mejoras Implementadas (v4.0) - Detección de Contenido Encriptado/DRM

**Detección Avanzada de Contenido Encriptado:**
- Validación MPEG-TS con detección de sync byte (0x47) para identificar segmentos válidos
- Detección automática de contenido DRM/encriptado durante descarga
- Sistema anti-loop que previene descargas infinitas de contenido protegido
- Identificación de tipos de encriptación: AES-128, DRM (Widevine, PlayReady), contenido tokenizado

**Funcionalidad "Solo Ver":**
- Botón "Solo Ver" para reproducir contenido encriptado sin descargarlo
- Reproductor HLS.js integrado en ventana emergente para contenido protegido
- Pre-análisis de URLs M3U8 para detectar encriptación antes de intentar descarga
- Endpoint `/analizar` para verificación previa de contenido

**Manejo Inteligente de Errores:**
- Detección temprana de contenido encriptado (primeros 10 segmentos fallidos)
- Cancelación automática de descargas cuando se detecta alta tasa de fallo (>95%)
- Mensajes de error específicos para diferentes tipos de protección
- Sugerencias automáticas para usar modo "Solo Ver" cuando sea apropiado

**Validación de Segmentos Mejorada:**
- Análisis hexadecimal de primeros bytes para identificar tipo de corrupción
- Detección de firmas específicas de encriptación (ej: `83e13899` para DRM)
- Identificación de respuestas HTML/404 en lugar de segmentos de video
- Logging detallado del tipo de contenido recibido (Content-Type, tamaño, headers)

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

# Master Playlist y selección de calidad
parse_master_playlist(m3u8_url)        # Analiza Master Playlist y extrae calidades disponibles
showQualitySelector(qualities, url)     # JavaScript: Muestra selector visual de calidades
selectQuality(qualityUrl, label)        # JavaScript: Selecciona calidad y actualiza URL
extractMetadata()                       # JavaScript: Extrae metadatos de URL M3U8

# Medición de tiempo y progreso
monitorDRMProgress(decryptId)           # JavaScript: Monitorea progreso de descifrado DRM en tiempo real
update_progress(progress_data)          # Callback para actualizar progreso de descifrado
decrypt_drm_content(file, workers, cb)  # Descifra contenido DRM con callback de progreso

# Detección de contenido encriptado/DRM
_validate_ts_segment(segment_path)      # Valida segmentos MPEG-TS por sync byte
_collect_all_segments()                 # Recopila segmentos de streams dinámicos/VOD
playOnlyM3U8()                          # JavaScript: Reproductor emergente para contenido encriptado
analizar_m3u8()                         # Flask: Pre-análisis de encriptación

# Gestión de archivos mejorada (GitIgnore)
- Exclusión automática: *.ts, decrypted_content/, download_state.json
- Inclusión selectiva: static/*.mp4, static/*.meta, static/*/*.mp4, static/*/*.meta
```

### Arquitectura de Master Playlist y Progreso en Tiempo Real

**Flujo de Master Playlist:**
1. **Detección Automática**: El sistema analiza automáticamente si una URL M3U8 es un Master Playlist
2. **Extracción de Calidades**: Parsea `#EXT-X-STREAM-INF` para obtener resolución, bitrate y URLs
3. **Selector Visual**: Presenta opciones de calidad en tarjetas con información detallada
4. **Selección Dinámica**: Al seleccionar una calidad, actualiza la URL automáticamente
5. **Integración Seamless**: Se integra con el flujo normal de descarga sin interrupciones

**Sistema de Progreso en Tiempo Real:**
1. **Callbacks de Progreso**: Sistema de callbacks que reporta progreso cada segmento procesado
2. **Estimación Inteligente**: Cálculos de ETA basados en velocidad actual de procesamiento
3. **Fases Separadas**: Progreso separado para Descifrado DRM y Unión FFmpeg
4. **Progreso FFmpeg**: Monitoreo en tiempo real del proceso de concatenación con `-progress pipe:1`
5. **Actualización Dinámica**: Frontend actualiza cada segundo para mostrar progreso preciso

**Componentes del Sistema de Tiempo:**
- **Descarga Normal**: Tiempo transcurrido, ETA, velocidad MB/s y seg/min
- **Descifrado DRM**: Progreso por segmento, tiempo restante estimado, velocidad de descifrado
- **Unión FFmpeg**: Progreso basado en tiempo, estimación de finalización, monitoreo de proceso
- **Visualización**: Barras de progreso, alertas de tiempo restante, estadísticas detalladas

### Arquitectura de Detección de Encriptación

**Flujo de Detección Multi-Nivel:**
1. **Pre-análisis** (`/analizar`): Verifica encriptación antes de descarga completa
2. **Validación de Headers**: Detecta `#EXT-X-KEY` en manifiestos M3U8
3. **Validación MPEG-TS**: Verifica sync byte `0x47` en segmentos descargados
4. **Detección de Patrones**: Identifica firmas de encriptación específicas
5. **Análisis de Tasa de Fallo**: Cancela automáticamente si >95% de segmentos fallan

**Tipos de Contenido Soportados:**
- ✅ **M3U8 No Encriptado**: Descarga completa y merge con FFmpeg
- ✅ **M3U8 Encriptado/DRM**: Modo "Solo Ver" con reproductor HLS.js
- ✅ **Streams Dinámicos**: Detección VOD vs LIVE con seguimiento de playlist
- ✅ **Contenido Tokenizado**: Detección y manejo de protección por tokens

### Notas de Desarrollo

- No se requiere proceso de build - aplicación Flask pura en Python
- Usa plantillas HTML incrustadas en `app.py` por simplicidad
- Gestión de descargas thread-safe con bloqueo apropiado
- Logging comprensivo para debugging de problemas de descarga
- Sistema de metadatos backward-compatible con descargas existentes
- Configuración centralizada en la parte superior de `app.py` para fácil personalización

### Resolución de Problemas Comunes

**Videos Incompletos (duración corta)**
- ✅ **Solucionado**: M3U8Downloader v4.2 detecta automáticamente streams dinámicos y recopila todos los segmentos
- Implementación de seguimiento de playlist hasta encontrar `#EXT-X-ENDLIST`
- Diferenciación entre contenido VOD y LIVE streams

**JavaScript Function Not Available Errors**
- ✅ **Solucionado**: Refactorización completa de event handlers
- Reemplazo de onclick inline con event listeners programáticos
- Uso de data attributes para pasar parámetros de funciones
- Funciones disponibles globalmente via `window` object

**Subprocess Import Errors (Pylance)**
- ✅ **Solucionado**: Import directo de funciones específicas
- `from subprocess import run, CalledProcessError, CompletedProcess`
- Manejo de tipos con `TYPE_CHECKING` para compatibilidad

**FFmpeg Merge Failures**
- ✅ **Solucionado**: Identificación de causa raíz como segmentos encriptados
- Implementación de validación MPEG-TS previa al merge
- Detección automática de contenido DRM/encriptado
- Sugerencia automática de modo "Solo Ver" para contenido protegido

**Infinite Download Loops**
- ✅ **Solucionado**: Sistema anti-loop con detección temprana
- Cancelación automática si primeros 10 segmentos fallan
- Cancelación automática si tasa de fallo >95%
- Logging detallado para identificar tipos de encriptación

### Estado Actual del Sistema

El sistema M3U8 Downloader está completamente funcional y robusto, con capacidades avanzadas para:
- **Descargar contenido M3U8** no protegido de alta calidad con selector de calidad automático
- **Detectar y manejar contenido encriptado/DRM** automáticamente con descifrado académico
- **Progreso en tiempo real** para todas las operaciones con estimaciones precisas de tiempo restante
- **Master Playlist inteligente** con selección visual de calidades (resolución, bitrate)
- **Monitoreo FFmpeg** con progreso detallado durante unión de segmentos
- **Gestión de archivos optimizada** con GitIgnore selectivo y organización automática
- **Proporcionar alternativa de visualización** para contenido protegido
- **Prevenir loops infinitos** y uso excesivo de recursos
- **Logging detallado** para debugging y análisis de problemas
- **Sistema de callbacks** para integración con aplicaciones externas

### Experiencia de Usuario Mejorada

**Durante Descarga Normal:**
```
🔄 Descargando...
[████████░░] 80%
Segmento 800 de 1000 (80%)
⏳ Tiempo restante: 2m 30s
📈 Velocidad: 15.4 MB/s
```

**Durante Descifrado DRM:**
```
🔄 Descifrando contenido DRM...
[██████░░░░] 60%
Segmento 420 de 700 (60%)
⏳ Tiempo restante estimado: 3m 15s
⏱️ Transcurrido: 7m 30s
📈 Velocidad: 45.2 seg/min
```

**Durante Unión FFmpeg:**
```
🔧 Uniendo segmentos descifrados...
[████████░░] 78%
FFmpeg progreso: 78%
⏳ Tiempo restante FFmpeg: 0m 25s
✅ Descifrado: 11m 45s
⏱️ Uniendo: 1m 30s
```

**Al Completar:**
```
🎉 Proceso Completado
⏱️ Tiempo total: 13m 15s
🔓 Descifrado: 11m 45s • 🔧 Unión: 1m 30s
📊 697 de 700 segmentos (3 omitidos por corrupción)
🔑 2 claves AES-128 obtenidas
```