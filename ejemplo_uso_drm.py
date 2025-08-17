#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de Uso del Módulo de Investigación DRM
==============================================

Este script muestra cómo utilizar el módulo DRM para investigación académica.
"""

from drm_research_module import create_research_session, analyze_drm_content
import json

def ejemplo_basico():
    """Ejemplo básico de análisis DRM"""
    print("🔬 EJEMPLO: Análisis básico de contenido DRM")
    print("-" * 50)
    
    # URL de ejemplo (reemplaza con tu contenido de investigación)
    m3u8_url = input("Introduce la URL M3U8 para analizar: ").strip()
    
    if not m3u8_url:
        print("❌ No se proporcionó URL")
        return
    
    try:
        # Crear sesión de investigación
        research_module = create_research_session("investigacion_tesis")
        
        # Realizar análisis completo
        print("🔍 Iniciando análisis DRM...")
        results = research_module.analyze_m3u8_drm(m3u8_url)
        
        # Mostrar resultados
        print("\n📊 RESULTADOS DEL ANÁLISIS:")
        print("=" * 30)
        
        if results['success']:
            print("✅ Análisis completado exitosamente")
            
            # Información del manifest
            manifest = results['manifest_info']
            print(f"📄 Segmentos encontrados: {len(manifest['segments'])}")
            print(f"🔐 Claves de encriptación: {len(manifest['encryption_keys'])}")
            
            # Métodos de encriptación
            encryption = results['encryption_analysis']
            print(f"🛡️ Métodos DRM: {encryption['methods_detected']}")
            print(f"📈 Nivel de complejidad: {encryption['complexity_level']}")
            
            # Hallazgos académicos
            print("\n🎓 HALLAZGOS PARA TESIS:")
            for finding in results['academic_findings']:
                print(f"• {finding}")
            
        else:
            print("❌ Error en el análisis")
            if 'error' in results:
                print(f"Error: {results['error']}")
        
        print(f"\n📁 Revisa los archivos generados en: investigacion_tesis/")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def ejemplo_avanzado():
    """Ejemplo avanzado con múltiples URLs"""
    print("🔬 EJEMPLO: Análisis comparativo de múltiple contenido DRM")
    print("-" * 60)
    
    urls = []
    print("Introduce URLs para análisis comparativo (Enter vacío para terminar):")
    
    while True:
        url = input(f"URL {len(urls) + 1}: ").strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("❌ No se proporcionaron URLs")
        return
    
    # Crear sesión de investigación
    research_module = create_research_session("analisis_comparativo")
    
    comparison_results = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n🔍 Analizando contenido {i}/{len(urls)}: {url[:50]}...")
        
        try:
            results = research_module.analyze_m3u8_drm(url)
            comparison_results.append(results)
            
            if results['success']:
                methods = results['encryption_analysis']['methods_detected']
                complexity = results['encryption_analysis']['complexity_level']
                print(f"✅ Métodos: {methods}, Complejidad: {complexity}")
            else:
                print("❌ Análisis falló")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Generar reporte comparativo
    generate_comparative_report(comparison_results, research_module)

def generate_comparative_report(results, research_module):
    """Genera reporte comparativo para la tesis"""
    print("\n📊 GENERANDO REPORTE COMPARATIVO...")
    
    comparative_data = {
        'total_analyzed': len(results),
        'successful_analyses': sum(1 for r in results if r.get('success', False)),
        'drm_types_found': set(),
        'complexity_distribution': {},
        'academic_summary': []
    }
    
    for result in results:
        if result.get('success', False):
            # Recolectar tipos de DRM
            methods = result['encryption_analysis']['methods_detected']
            comparative_data['drm_types_found'].update(methods)
            
            # Distribución de complejidad
            complexity = result['encryption_analysis']['complexity_level']
            comparative_data['complexity_distribution'][complexity] = \
                comparative_data['complexity_distribution'].get(complexity, 0) + 1
    
    # Convertir set a list para JSON
    comparative_data['drm_types_found'] = list(comparative_data['drm_types_found'])
    
    # Generar observaciones académicas
    comparative_data['academic_summary'].append(
        f"Se analizaron {comparative_data['total_analyzed']} fuentes de contenido DRM"
    )
    comparative_data['academic_summary'].append(
        f"Tasa de éxito del análisis: {comparative_data['successful_analyses']/comparative_data['total_analyzed']*100:.1f}%"
    )
    comparative_data['academic_summary'].append(
        f"Tipos de DRM identificados: {', '.join(comparative_data['drm_types_found'])}"
    )
    
    # Guardar reporte comparativo
    import os
    from datetime import datetime
    
    report_file = os.path.join(research_module.research_dir, "analysis", 
                              f"comparative_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(comparative_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Reporte comparativo guardado: {report_file}")
    
    # Mostrar resumen
    print("\n📈 RESUMEN COMPARATIVO:")
    for summary in comparative_data['academic_summary']:
        print(f"• {summary}")

def menu_principal():
    """Menú principal de ejemplos"""
    while True:
        print("\n🔬 MÓDULO DE INVESTIGACIÓN DRM - EJEMPLOS")
        print("=" * 45)
        print("1. Análisis básico de contenido DRM")
        print("2. Análisis comparativo (múltiples URLs)")
        print("3. Ver información del módulo")
        print("0. Salir")
        
        opcion = input("\nSelecciona una opción: ").strip()
        
        if opcion == "1":
            ejemplo_basico()
        elif opcion == "2":
            ejemplo_avanzado()
        elif opcion == "3":
            mostrar_info_modulo()
        elif opcion == "0":
            print("👋 ¡Éxito en tu investigación!")
            break
        else:
            print("❌ Opción no válida")

def mostrar_info_modulo():
    """Muestra información sobre el módulo"""
    print("\n📚 INFORMACIÓN DEL MÓDULO DRM")
    print("=" * 35)
    print("🎯 Propósito: Investigación académica de sistemas DRM")
    print("📖 Uso: Desarrollo de tesis y análisis educativo")
    print("🔧 Funcionalidades:")
    print("   • Análisis de manifiestos M3U8")
    print("   • Detección de métodos de encriptación")
    print("   • Clasificación de complejidad DRM")
    print("   • Documentación automática para tesis")
    print("   • Generación de reportes académicos")
    print("\n📁 Estructura de archivos generados:")
    print("   research_dir/")
    print("   ├── segments/     (segmentos descargados)")
    print("   ├── keys/         (información de claves)")
    print("   ├── decrypted/    (contenido descifrado)")
    print("   ├── analysis/     (reportes y análisis)")
    print("   └── research_log_*.log (logs detallados)")

if __name__ == "__main__":
    print("🎓 Módulo de Investigación DRM para Tesis")
    print("Desarrollado para análisis académico de sistemas DRM")
    print()
    
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")