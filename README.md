# 🚀 Descargador de Videos M3U8 Súper Rápido

Un descargador de videos M3U8 optimizado para conexiones de alta velocidad con interfaz web moderna y tracking en tiempo real.

## ✨ Características

### 🏎️ **Velocidad Extrema**
- **1000 workers simultáneos** para máximo paralelismo
- **Chunks de 8MB** para transferencia súper rápida
- **HTTPAdapter optimizado** con pools grandes
- **Headers Brotli** para máxima compresión
- **Velocidades de 20-50+ MB/s** en conexiones rápidas

### 📊 **Monitoreo en Tiempo Real**
- **Velocidad de descarga** en MB/s y KB/s
- **Tiempo transcurrido** en formato HH:MM:SS
- **Tiempo estimado restante** con cálculo inteligente
- **Progreso por segmentos** con contador visual
- **Dashboard de estadísticas** completo

### 🔧 **Funciones Avanzadas**
- **Reanudación de descargas** interrumpidas
- **Descargas simultáneas** múltiples
- **Historial completo** de descargas
- **Gestión inteligente** de archivos duplicados
- **Limpieza automática** de archivos temporales

### 🎨 **Interfaz Moderna**
- **Diseño responsivo** para móvil y desktop
- **Tema oscuro** elegante
- **Notificaciones** en tiempo real
- **Controles intuitivos** de pausa/cancelación
- **Reproductor fijo**: Dimensiones consistentes (600x400px) para mejor experiencia visual

### 📊 Gestión avanzada
- **Descargas múltiples**: Soporta múltiples descargas simultáneas
- **Cancelación de descargas**: Cancela descargas en progreso con confirmación
- **Progreso en tiempo real**: Barras de progreso y porcentajes actualizados
- **Estados visuales**: Indicadores claros (descargando, completado, error, cancelado)

### 📁 Historial y archivos
- **Historial automático**: Los archivos descargados aparecen automáticamente
- **Gestión de archivos**: Elimina archivos con botón de borrado y confirmación
- **Descarga directa**: Enlaces directos para descargar archivos MP4
- **Interfaz organizada**: Layout responsive con sidebar para navegación

## 🛠️ Instalación

### Requisitos previos
- Python 3.7 o superior
- FFmpeg instalado y configurado en PATH
- Dependencias de Python (ver requirements.txt)

### Pasos de instalación

1. **Clona el repositorio**:
```bash
git clone https://github.com/kevinarauz/descargar-videos.git
cd descargar-videos
```

2. **Instala las dependencias**:
```bash
pip install flask requests tqdm
```

3. **Instala FFmpeg**:
   - **Windows**: Descarga desde [FFmpeg.org](https://ffmpeg.org/download.html) y agrega al PATH
   - **Linux**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`

4. **Verifica la instalación de FFmpeg**:
```bash
ffmpeg -version
```

## 🚀 Uso

### Iniciar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Funcionalidades principales

#### 🎮 Reproducir video
1. Pega la URL M3U8 en el campo de entrada
2. Haz clic en **"Reproducir"**
3. El video se mostrará en el reproductor integrado

#### 📥 Descargar video
1. Pega la URL M3U8 en el campo de entrada
2. (Opcional) Especifica un nombre para el archivo
3. Haz clic en **"Descargar MP4"**
4. Monitorea el progreso en la sección "Descargas activas"

#### ❌ Cancelar descarga
1. En "Descargas activas", haz clic en **"Cancelar"** junto a la descarga
2. Confirma la acción en el popup
3. La descarga se detendrá y marcará como cancelada

#### 🗑️ Eliminar archivos
1. En el historial, haz clic en el botón **🗑️** junto al archivo
2. Confirma la eliminación en el popup
3. El archivo se eliminará permanentemente del servidor

## 🏗️ Estructura del proyecto

```
descargar-videos/
├── app.py              # Aplicación Flask principal
├── test.py             # Clase M3U8Downloader
├── README.md           # Este archivo
├── .gitignore          # Archivos ignorados por Git
├── static/             # Archivos MP4 descargados (no en Git)
├── temp_segments/      # Segmentos temporales (no en Git)
└── __pycache__/        # Cache de Python (no en Git)
```

## 🔧 Configuración

### Variables de entorno
- `FLASK_ENV`: Entorno de ejecución (development/production)
- `FLASK_DEBUG`: Modo debug (True/False)

### Configuración de la aplicación
- **Puerto**: 5000 (configurable en `app.py`)
- **Host**: 0.0.0.0 (accesible desde cualquier interfaz)
- **Workers máximos**: 20 hilos de descarga simultáneos

## 🚨 Solución de problemas

### Error: "ffmpeg no encontrado"
- Verifica que FFmpeg esté instalado y en el PATH del sistema
- Reinicia la terminal después de instalar FFmpeg

### Error: "No se pueden descargar segmentos"
- Verifica la conectividad a internet
- Comprueba que la URL M3U8 sea válida y esté accesible
- Algunos videos pueden estar protegidos o cifrados

### La página no carga
- Verifica que el puerto 5000 no esté en uso
- Comprueba que Flask esté instalado correctamente
- Revisa los logs en la consola para errores específicos

## 🔒 Seguridad

- Validación de nombres de archivo para prevenir ataques
- Verificación de rutas para evitar path traversal
- Limpieza automática de recursos temporales
- Manejo seguro de eliminación de archivos

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENSE para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📞 Soporte

Si encuentras problemas o tienes preguntas, por favor abre un issue en el repositorio de GitHub.

---

**Desarrollado con ❤️ usando Flask, Python, Bootstrap y hls.js**