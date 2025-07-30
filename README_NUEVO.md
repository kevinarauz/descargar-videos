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

## 🛠️ Instalación

### 1. **Clonar el repositorio**
```bash
git clone https://github.com/kevinarauz/descargar-videos.git
cd descargar-videos
```

### 2. **Instalar dependencias Python**
```bash
pip install -r requirements.txt
```

### 3. **Instalar FFmpeg**

**Windows:**
```bash
# Con chocolatey
choco install ffmpeg

# O descargar desde: https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

## 🚀 Uso

### **Ejecutar la aplicación**
```bash
python app.py
```

### **Abrir en el navegador**
```
http://localhost:5000
```

### **Usar la interfaz**
1. **Pegar URL M3U8** en el campo de entrada
2. **Opcional:** Especificar nombre del archivo
3. **Hacer clic en "Descargar"**
4. **Monitorear progreso** en tiempo real
5. **Descargar el MP4** cuando esté listo

## 📁 Estructura del Proyecto

```
descargar-videos/
├── app.py              # Aplicación Flask principal
├── test.py             # Motor de descarga M3U8 optimizado
├── requirements.txt    # Dependencias Python
├── README.md          # Este archivo
├── static/            # Videos descargados (se crea automáticamente)
├── temp_segments/     # Archivos temporales (se limpia automáticamente)
└── download_state.json # Estado de descargas (se crea automáticamente)
```

## ⚙️ Configuración Avanzada

### **Variables de Entorno**
```bash
# Puerto del servidor (por defecto: 5000)
export PORT=8080

# Máximo de descargas simultáneas (por defecto: 5)
export MAX_CONCURRENT_DOWNLOADS=10
```

### **Optimización para tu Internet**
En `app.py` línea 3307, puedes ajustar:
```python
max_workers=1000  # Aumentar para internet súper rápido
                  # Reducir si hay errores de conexión
```

## 🔧 Troubleshooting

### **Velocidad lenta (menos de 5 MB/s)**
- Aumentar `max_workers` en `app.py`
- Verificar que FFmpeg esté instalado
- Comprobar conexión a internet

### **Errores de conexión**
- Reducir `max_workers` a 500 o menos
- Verificar que la URL M3U8 sea válida
- Comprobar firewall/antivirus

### **Videos no se descargan**
- Verificar instalación de FFmpeg
- Comprobar permisos de escritura
- Revisar logs en la consola

## 📈 Rendimiento

### **Velocidades típicas por tipo de internet:**
- **Fibra 1Gbps:** 50-80 MB/s
- **Cable 500Mbps:** 30-50 MB/s  
- **Cable 100Mbps:** 10-15 MB/s
- **ADSL 50Mbps:** 5-8 MB/s

### **Optimizaciones aplicadas:**
- ✅ Chunks de 8MB para máxima transferencia
- ✅ 1000 conexiones simultáneas
- ✅ Compresión Brotli habilitada
- ✅ Pools de conexiones optimizados
- ✅ Buffers de escritura de 8MB
- ✅ Sin proxies del sistema

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [Flask](https://flask.palletsprojects.com/) - Framework web
- [Requests](https://requests.readthedocs.io/) - HTTP library
- [FFmpeg](https://ffmpeg.org/) - Procesamiento de video
- [TQDM](https://tqdm.github.io/) - Barras de progreso

## 📞 Soporte

¿Problemas o preguntas? 
- Abrir un [Issue](https://github.com/kevinarauz/descargar-videos/issues)
- Contactar: [kevinarauz](https://github.com/kevinarauz)

---

**¡Disfruta descargando videos a velocidad extrema! 🚀⚡**
