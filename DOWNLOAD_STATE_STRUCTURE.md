# 📄 Estructura del archivo download_state.json

## 🎯 Propósito
Este archivo mantiene el estado persistente de las descargas activas, la cola de descargas y el estado general del sistema.

## 🏗️ Estructura JSON

```json
{
  "multi_progress": {
    "download_id_1": {
      "url": "https://example.com/video.m3u8",
      "output_file": "video.mp4",
      "status": "downloading|done|error|cancelled|paused",
      "current": 150,
      "total": 300,
      "percentage": 50.0,
      "start_time": 1642781234,
      "end_time": null,
      "error": null,
      "can_resume": true,
      "temp_dir": "temp_segments",
      "quality": "best"
    }
  },
  "download_queue": [
    {
      "url": "https://example.com/video2.m3u8",
      "output_file": "video2.mp4",
      "quality": "best",
      "added_time": 1642781234
    }
  ],
  "queue_running": false
}
```

## 📋 Descripción de campos

### multi_progress
Objeto que contiene el estado de cada descarga activa, indexado por `download_id`.

**Campos de cada descarga:**
- `url`: URL del archivo M3U8 original
- `output_file`: Nombre del archivo de salida (MP4)
- `status`: Estado actual de la descarga
  - `downloading`: Descarga en progreso
  - `done`: Descarga completada
  - `error`: Error durante la descarga
  - `cancelled`: Descarga cancelada por el usuario
  - `paused`: Descarga pausada (puede reanudarse)
- `current`: Número de segmentos descargados
- `total`: Número total de segmentos
- `percentage`: Porcentaje de progreso (0-100)
- `start_time`: Timestamp de inicio de descarga
- `end_time`: Timestamp de finalización (null si no ha terminado)
- `error`: Mensaje de error (null si no hay error)
- `can_resume`: Indica si la descarga puede reanudarse
- `temp_dir`: Directorio temporal para segmentos
- `quality`: Calidad seleccionada para la descarga

### download_queue
Array que contiene las descargas en cola esperando a ser procesadas.

**Campos de cada elemento en cola:**
- `url`: URL del archivo M3U8
- `output_file`: Nombre del archivo de salida
- `quality`: Calidad seleccionada
- `added_time`: Timestamp cuando se agregó a la cola

### queue_running
Booleano que indica si el procesador de cola está activo.

## 🔄 Ciclo de vida

1. **Inicio de descarga**: Se crea entrada en `multi_progress` con status `downloading`
2. **Progreso**: Se actualiza `current` y `percentage` durante la descarga
3. **Finalización**: Status cambia a `done`, `error`, `cancelled` o `paused`
4. **Persistencia**: El archivo se guarda automáticamente en cada cambio de estado

## 🛠️ Funciones relacionadas

- `save_download_state()`: Guarda el estado actual en el archivo
- `load_download_state()`: Carga el estado desde el archivo al iniciar
- Al cargar, las descargas con status `downloading` se marcan como `paused`

## 📁 Ubicación
El archivo se encuentra en la raíz del proyecto: `download_state.json`

## ⚠️ Notas importantes
- El archivo se sobrescribe completamente en cada actualización
- Si se corrompe, se inicializa con estructura vacía
- Las descargas `downloading` se convierten a `paused` al reiniciar la aplicación
