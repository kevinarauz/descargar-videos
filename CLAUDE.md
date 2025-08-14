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

**Clase M3U8 Downloader (`test.py`)**
- Lógica principal de descarga para playlists M3U8
- Soporta descarga paralela de segmentos de alto rendimiento (workers configurables)
- Implementa lógica de reintentos y pooling de conexiones para confiabilidad
- Maneja playlists maestras y selección de calidad automáticamente
- Usa FFmpeg para la fusión final de video

**Interfaz Web (`index.html` incrustado en `app.py`)**
- UI responsiva moderna con seguimiento de progreso en tiempo real
- Soporta múltiples descargas simultáneas con barras de progreso visuales
- Reproductor de video M3U8 integrado usando hls.js
- Historial de descargas y gestión de archivos

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
- `temp_segments/` - Segmentos TS temporales durante descarga (excluido de git)
- `download_state.json` - Estado persistente de descarga (excluido de git)

### Gestión de Estado

La aplicación mantiene el estado de descarga en `download_state.json` con la siguiente estructura:
- `multi_progress`: Descargas activas/completadas con información de progreso
- `download_queue`: Descargas en cola esperando para iniciar
- `queue_running`: Estado del procesador de cola

Las descargas interrumpidas por reinicio de aplicación se marcan automáticamente como "pausadas" y pueden reanudarse.

### Constantes de Configuración

Configuración clave en `app.py`:
- `MAX_CONCURRENT_DOWNLOADS = 5` - Máximo de descargas simultáneas
- `DEFAULT_QUALITY = 'best'` - Selección de calidad para descargas
- Cantidad de workers configurable por descarga (defecto 30, máximo 1000)

### Consideraciones de Seguridad

- Validación de entrada para URLs M3U8 y nombres de archivo
- Protección contra path traversal para operaciones de archivo
- Sanitización segura de nombres de archivo
- Limpieza de archivos temporales en errores

### Endpoints de API

- `GET /` - Interfaz principal
- `POST /download` - Iniciar nueva descarga
- `GET /progress/<download_id>` - Obtener progreso de descarga
- `POST /cancel/<download_id>` - Cancelar descarga activa
- `GET /files` - Listar archivos descargados
- `POST /delete_file` - Eliminar archivo descargado
- `GET /download_file/<filename>` - Descargar archivo al cliente

### Manejo de Errores

- Reintentos automáticos para descargas de segmentos fallidas
- Degradación elegante cuando faltan segmentos
- Detección y reporte de errores de FFmpeg
- Manejo de timeouts de red con límites configurables

### Notas de Desarrollo

- No se requiere proceso de build - aplicación Flask pura en Python
- Usa plantillas HTML incrustadas en `app.py` por simplicidad
- Gestión de descargas thread-safe con bloqueo apropiado
- Logging comprensivo para debugging de problemas de descarga