#!/usr/bin/env python3
"""
Test simple para verificar la función de historial
"""
import sys
import os

# Agregar el directorio actual al path para importar app
sys.path.insert(0, os.path.dirname(__file__))

# Importar la función que necesitamos probar
from app import load_video_metadata, format_file_size

def test_simple_historial():
    """Prueba simple de la lógica del historial"""
    print("🧪 TEST SIMPLE DE LÓGICA DE HISTORIAL")
    print("=" * 50)
    
    import glob
    import os
    from datetime import datetime
    
    # Simular exactamente lo que hace el endpoint
    archivos = []
    static_dir = 'static'
    
    print(f"📂 Buscando archivos en: {static_dir}")
    
    if os.path.exists(static_dir):
        mp4_files = glob.glob(os.path.join(static_dir, '*.mp4'))
        print(f"📄 Archivos encontrados: {len(mp4_files)}")
        
        for archivo in mp4_files:
            nombre_archivo = os.path.basename(archivo)
            print(f"\n📹 Procesando: {nombre_archivo}")
            
            try:
                file_stats = os.stat(archivo)
                fecha_modificacion = datetime.fromtimestamp(file_stats.st_mtime)
                
                # Buscar URL en metadata (lógica del endpoint corregido)
                url_asociada = None
                fecha_descarga = None
                
                try:
                    metadata = load_video_metadata(nombre_archivo)
                    if metadata:
                        url_asociada = metadata.get('url')
                        fecha_descarga = metadata.get('download_date')
                        print(f"   📋 Metadata cargada - URL: {url_asociada}")
                        print(f"   📋 Fecha descarga: {fecha_descarga}")
                        
                        # Mostrar toda la metadata
                        print(f"   📋 Metadata completa:")
                        for key, value in metadata.items():
                            print(f"      {key}: {value}")
                    else:
                        print(f"   ⚠️ load_video_metadata retornó None")
                except Exception as meta_error:
                    print(f"   ❌ Error cargando metadata: {meta_error}")
                
                # Usar fecha de descarga si está disponible
                fecha_para_mostrar = fecha_modificacion.strftime('%d/%m/%Y %H:%M')
                timestamp_para_ordenar = int(file_stats.st_mtime)
                
                if fecha_descarga:
                    try:
                        dt_descarga = datetime.fromisoformat(fecha_descarga.replace('Z', '+00:00').replace('+00:00', ''))
                        fecha_para_mostrar = dt_descarga.strftime('%d/%m/%Y %H:%M')
                        timestamp_para_ordenar = int(dt_descarga.timestamp())
                        print(f"   📅 Usando fecha de metadata: {fecha_para_mostrar}")
                    except Exception as date_error:
                        print(f"   ⚠️ Error parseando fecha de metadata: {date_error}")
                
                archivo_info = {
                    'archivo': nombre_archivo,
                    'tamaño': format_file_size(file_stats.st_size),
                    'tamaño_bytes': file_stats.st_size,
                    'fecha': fecha_para_mostrar,
                    'fecha_timestamp': timestamp_para_ordenar,
                    'url': url_asociada
                }
                
                archivos.append(archivo_info)
                print(f"   ✅ Agregado al historial")
                print(f"      - Archivo: {archivo_info['archivo']}")
                print(f"      - Tamaño: {archivo_info['tamaño']}")
                print(f"      - Fecha: {archivo_info['fecha']}")
                print(f"      - URL: {archivo_info['url'] or 'NO ENCONTRADA'}")
                
            except Exception as e:
                print(f"   ❌ Error procesando {archivo}: {e}")
        
        # Ordenar como en el endpoint
        archivos.sort(key=lambda x: x['fecha_timestamp'], reverse=True)
        
        print(f"\n📊 HISTORIAL FINAL GENERADO:")
        print(f"Total archivos: {len(archivos)}")
        
        for i, archivo in enumerate(archivos, 1):
            url_status = "✅" if archivo['url'] else "❌"
            print(f"{i}. 📄 {archivo['archivo']}")
            print(f"   📊 {archivo['tamaño']} - 📅 {archivo['fecha']}")
            print(f"   🌐 URL: {url_status} {archivo['url'] or 'FALTANTE'}")
        
        # Simular la respuesta JSON que enviaría el endpoint
        response_data = {
            'success': True,
            'historial': archivos
        }
        
        print(f"\n📤 RESPUESTA JSON QUE ENVIARÍA EL ENDPOINT:")
        import json
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
    else:
        print(f"❌ Directorio {static_dir} no existe")

if __name__ == "__main__":
    test_simple_historial()
    print(f"\n" + "=" * 60)
    print("🎯 RESULTADO:")
    print("Si ves URLs con ✅, el backend está funcionando correctamente")
    print("Si ves URLs con ❌, hay un problema en load_video_metadata()")
    print("Si todas las URLs están correctas, el problema está en el frontend")
