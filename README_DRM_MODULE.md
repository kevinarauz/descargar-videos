# Módulo de Investigación DRM para Tesis Académica

## 🎓 Propósito

Este módulo está diseñado específicamente para **investigación académica** y **desarrollo de tesis** sobre sistemas de gestión de derechos digitales (DRM) en contenido de streaming.

## ⚠️ Aviso Importante

**USO EXCLUSIVAMENTE ACADÉMICO**: Este módulo está destinado únicamente para:
- Investigación educativa
- Desarrollo de tesis universitarias
- Análisis académico de protocolos DRM
- Estudios de seguridad en entornos controlados

## 🛠️ Instalación

### Dependencias Requeridas

```bash
pip install requests cryptography
```

### Estructura de Archivos

```
drm_research_module.py    # Módulo principal
ejemplo_uso_drm.py        # Script de ejemplos
README_DRM_MODULE.md      # Esta documentación
```

## 📚 Uso Básico

### Importar el Módulo

```python
from drm_research_module import create_research_session, analyze_drm_content
```

### Análisis Básico

```python
# Crear sesión de investigación
research_module = create_research_session("mi_investigacion")

# Analizar contenido DRM
results = research_module.analyze_m3u8_drm("https://ejemplo.com/video.m3u8")

# Revisar resultados
if results['success']:
    print("Análisis completado exitosamente")
    print(f"Métodos DRM: {results['encryption_analysis']['methods_detected']}")
```

### Función de Conveniencia

```python
# Análisis rápido
results = analyze_drm_content("https://ejemplo.com/video.m3u8", "directorio_investigacion")
```

## 🔬 Funcionalidades del Módulo

### 1. Análisis de Manifiestos M3U8
- ✅ Detección de tipo de playlist (master/media)
- ✅ Extracción de información de segmentos
- ✅ Identificación de claves de encriptación
- ✅ Análisis de estructura del manifest

### 2. Clasificación de DRM
- ✅ **AES-128**: Encriptación estándar básica
- ✅ **SAMPLE-AES**: Encriptación parcial de segmentos
- ✅ **Common Encryption (CENC)**: DRM avanzado
- ✅ **Detección automática** de nivel de complejidad

### 3. Análisis de Segmentos
- ✅ Descarga de segmentos para análisis
- ✅ Detección de patrones de encriptación
- ✅ Análisis de características estructurales
- ✅ Identificación de sync bytes MPEG-TS

### 4. Documentación Académica
- ✅ Generación automática de reportes
- ✅ Logging detallado para trazabilidad
- ✅ Exportación de datos en formato JSON
- ✅ Hallazgos estructurados para tesis

## 📁 Estructura de Salida

El módulo genera la siguiente estructura de archivos:

```
research_dir/
├── segments/              # Segmentos descargados para análisis
│   ├── segment_000.ts
│   ├── segment_001.ts
│   └── ...
├── keys/                  # Información de claves (cuando disponible)
├── decrypted/            # Contenido descifrado (para casos compatibles)
├── analysis/             # Reportes y análisis
│   ├── drm_analysis_TIMESTAMP.json
│   ├── academic_report_TIMESTAMP.txt
│   └── comparative_report_TIMESTAMP.json
└── research_log_TIMESTAMP.log  # Log detallado
```

## 📊 Ejemplo de Resultados

```json
{
  "url": "https://ejemplo.com/video.m3u8",
  "timestamp": "2024-01-15T10:30:00",
  "encryption_analysis": {
    "methods_detected": ["AES-128"],
    "complexity_level": "BASIC",
    "drm_type": "AES_STANDARD"
  },
  "segment_analysis": {
    "total_segments": 180,
    "segments_analyzed": 5
  },
  "academic_findings": [
    "Nivel de complejidad DRM detectado: BASIC",
    "Métodos de encriptación identificados: AES-128",
    "Segmentos analizados: 5 de 180 totales"
  ]
}
```

## 🚀 Ejecutar Ejemplos

### Script de Ejemplos Interactivo

```bash
python ejemplo_uso_drm.py
```

Este script incluye:
- **Análisis básico**: Un solo contenido DRM
- **Análisis comparativo**: Múltiples URLs para comparación
- **Reportes académicos**: Generación automática

### Ejemplo Programático

```python
from drm_research_module import DRMResearchModule

# Crear instancia del módulo
module = DRMResearchModule(research_dir="mi_tesis_drm")

# Analizar contenido
results = module.analyze_m3u8_drm("https://streaming.example.com/video.m3u8")

# Acceder a resultados específicos
if results['success']:
    encryption_methods = results['encryption_analysis']['methods_detected']
    complexity = results['encryption_analysis']['complexity_level']
    
    print(f"DRM detectado: {encryption_methods}")
    print(f"Complejidad: {complexity}")
    
    # Revisar hallazgos académicos
    for finding in results['academic_findings']:
        print(f"📚 {finding}")
```

## 🎯 Casos de Uso para Tesis

### 1. Análisis Comparativo de Plataformas
```python
platforms = {
    "Plataforma A": "https://platforma-a.com/content.m3u8",
    "Plataforma B": "https://platforma-b.com/video.m3u8",
    "Plataforma C": "https://platforma-c.com/stream.m3u8"
}

comparison_data = {}
for name, url in platforms.items():
    results = analyze_drm_content(url, f"tesis_{name.lower()}")
    comparison_data[name] = results['encryption_analysis']
```

### 2. Evolución Temporal del DRM
```python
# Analizar mismo contenido en diferentes momentos
timestamps = []
for week in range(4):  # 4 semanas
    results = analyze_drm_content(url, f"week_{week}")
    timestamps.append(results)
    time.sleep(604800)  # 1 semana
```

### 3. Clasificación de Contenido por Complejidad
```python
content_urls = ["url1", "url2", "url3", ...]
complexity_distribution = {"BASIC": 0, "INTERMEDIATE": 0, "ADVANCED": 0}

for url in content_urls:
    results = analyze_drm_content(url)
    if results['success']:
        complexity = results['encryption_analysis']['complexity_level']
        complexity_distribution[complexity] += 1
```

## 📈 Métricas para Investigación

El módulo proporciona métricas cuantificables para tu tesis:

- **Tasa de detección DRM**: % de contenido con protección detectada
- **Distribución de métodos**: AES-128 vs SAMPLE-AES vs CENC
- **Complejidad promedio**: Clasificación de nivel de protección
- **Tiempo de análisis**: Eficiencia del proceso de detección
- **Tasa de éxito**: % de análisis completados exitosamente

## 🔍 Debugging y Desarrollo

### Logging Detallado
El módulo genera logs comprensivos:

```
2024-01-15 10:30:15 - [DRM RESEARCH] - INFO - Iniciando análisis DRM
2024-01-15 10:30:16 - [DRM RESEARCH] - INFO - Manifest analizado: 180 segmentos, 1 claves
2024-01-15 10:30:17 - [DRM RESEARCH] - INFO - Analizando segmento 1/5
```

### Validación de Resultados
```python
# Verificar consistencia de resultados
def validate_analysis(results):
    assert results['success'] == True
    assert 'encryption_analysis' in results
    assert 'academic_findings' in results
    assert len(results['academic_findings']) > 0
```

## 🎓 Consideraciones Académicas

### Para tu Tesis
1. **Metodología**: Documenta el proceso de análisis utilizado
2. **Limitaciones**: Reconoce limitaciones del enfoque técnico
3. **Reproducibilidad**: Incluye datos suficientes para replicar
4. **Ética**: Mantén el enfoque en investigación educativa

### Estructura Sugerida de Capítulos
1. **Introducción a DRM**: Historia y evolución
2. **Metodología de Análisis**: Uso de este módulo
3. **Resultados**: Hallazgos del análisis
4. **Discusión**: Implicaciones académicas
5. **Conclusiones**: Aportes al conocimiento

## 📞 Soporte

Este módulo está diseñado para ser autocontenido y bien documentado. Para investigación académica adicional:

1. Revisa los logs detallados generados
2. Examina los archivos JSON de resultados
3. Utiliza los reportes académicos como base
4. Extiende el módulo según tus necesidades específicas

## ⚖️ Limitaciones y Consideraciones Legales

- **Solo para investigación académica**
- **No para uso comercial o distribución**
- **Respeta términos de servicio** de las plataformas analizadas
- **Enfoque educativo** únicamente

---

**Desarrollado para investigación académica en sistemas DRM**
**Versión 1.0 - Módulo de Tesis**