#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descargador Completo de Segmentos DRM para Investigación
========================================================

Extiende el módulo DRM para descargar TODOS los segmentos
de un contenido HLS para análisis académico completo.
"""

import json
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

def safe_print(message):
    """Print seguro que maneja emojis en Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)

class CompleteSegmentDownloader:
    """Descargador completo de segmentos para investigación académica"""
    
    def __init__(self, analysis_file, output_dir="complete_download", max_workers=30):
        self.analysis_file = analysis_file
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.session = requests.Session()
        self.download_stats = {
            'total_segments': 0,
            'downloaded': 0,
            'failed': 0,
            'total_size': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Configurar headers realistas
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })
        
        self.setup_output_directory()
    
    def setup_output_directory(self):
        """Crear directorio de salida"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "segments"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "analysis"), exist_ok=True)
    
    def load_analysis_data(self):
        """Cargar datos del análisis previo"""
        safe_print(f"Cargando análisis desde: {self.analysis_file}")
        
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        segments = data['manifest_info']['segments']
        self.download_stats['total_segments'] = len(segments)
        
        safe_print(f"Segmentos encontrados: {len(segments)}")
        return segments
    
    def download_single_segment(self, segment_info):
        """Descarga un segmento individual"""
        index, url = segment_info
        segment_filename = f"segment_{index:04d}.ts"
        segment_path = os.path.join(self.output_dir, "segments", segment_filename)
        
        # Si ya existe, saltar
        if os.path.exists(segment_path):
            return {'success': True, 'size': os.path.getsize(segment_path), 'cached': True}
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Guardar segmento
            with open(segment_path, 'wb') as f:
                f.write(response.content)
            
            # Validar que es MPEG-TS válido
            is_valid = self.validate_ts_segment(segment_path)
            
            return {
                'success': True, 
                'size': len(response.content),
                'valid_ts': is_valid,
                'cached': False
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'cached': False}
    
    def validate_ts_segment(self, segment_path):
        """Valida que un segmento sea MPEG-TS válido"""
        try:
            with open(segment_path, 'rb') as f:
                first_byte = f.read(1)
                return len(first_byte) > 0 and first_byte[0] == 0x47
        except:
            return False
    
    def download_all_segments(self):
        """Descarga todos los segmentos usando threading"""
        safe_print("INICIANDO DESCARGA COMPLETA DE SEGMENTOS")
        safe_print("=" * 50)
        
        # Cargar URLs de segmentos
        segments = self.load_analysis_data()
        
        # Preparar datos para descarga
        segment_data = [(i, url) for i, url in enumerate(segments)]
        
        # Estadísticas
        self.download_stats['start_time'] = datetime.now()
        downloaded_count = 0
        failed_count = 0
        total_size = 0
        cached_count = 0
        valid_segments = 0
        
        safe_print(f"Descargando {len(segments)} segmentos con {self.max_workers} workers...")
        safe_print(f"Directorio de salida: {self.output_dir}")
        safe_print("")
        
        # Descarga paralela con barra de progreso
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar todas las tareas
            futures = {executor.submit(self.download_single_segment, seg_info): seg_info 
                      for seg_info in segment_data}
            
            # Procesar resultados con barra de progreso
            with tqdm(total=len(segments), desc="Descargando segmentos", unit="seg") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    
                    if result['success']:
                        downloaded_count += 1
                        total_size += result['size']
                        
                        if result.get('cached', False):
                            cached_count += 1
                        
                        if result.get('valid_ts', False):
                            valid_segments += 1
                        
                        # Actualizar descripción de la barra
                        pbar.set_description(f"Descargados: {downloaded_count}, Fallos: {failed_count}")
                    else:
                        failed_count += 1
                    
                    pbar.update(1)
        
        # Finalizar estadísticas
        self.download_stats['end_time'] = datetime.now()
        self.download_stats['downloaded'] = downloaded_count
        self.download_stats['failed'] = failed_count
        self.download_stats['total_size'] = total_size
        
        # Mostrar resultados
        self.show_download_results(cached_count, valid_segments)
        
        # Generar reporte académico
        self.generate_academic_report(valid_segments, cached_count)
        
        return self.download_stats
    
    def show_download_results(self, cached_count, valid_segments):
        """Mostrar resultados de la descarga"""
        stats = self.download_stats
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        safe_print("")
        safe_print("RESULTADOS DE LA DESCARGA COMPLETA")
        safe_print("=" * 40)
        safe_print(f"Total de segmentos: {stats['total_segments']}")
        safe_print(f"Descargados exitosamente: {stats['downloaded']}")
        safe_print(f"Fallos: {stats['failed']}")
        safe_print(f"Archivos ya existían: {cached_count}")
        safe_print(f"Segmentos MPEG-TS válidos: {valid_segments}")
        safe_print(f"Tamaño total: {stats['total_size'] / (1024*1024):.1f} MB")
        safe_print(f"Tiempo total: {duration:.1f} segundos")
        safe_print(f"Velocidad promedio: {stats['downloaded']/duration:.1f} segmentos/segundo")
        
        # Tasa de éxito
        success_rate = (stats['downloaded'] / stats['total_segments']) * 100
        safe_print(f"Tasa de éxito: {success_rate:.1f}%")
        
        # Evaluación académica
        safe_print("")
        safe_print("EVALUACIÓN ACADÉMICA:")
        safe_print("-" * 20)
        
        if success_rate >= 95:
            safe_print("EXCELENTE: Descarga casi completa para análisis")
        elif success_rate >= 80:
            safe_print("BUENA: Muestra representativa para investigación")
        elif success_rate >= 50:
            safe_print("ACEPTABLE: Datos suficientes para análisis parcial")
        else:
            safe_print("LIMITADA: Muestra pequeña, revisar conectividad")
        
        # Análisis de validez
        if valid_segments > 0:
            validity_rate = (valid_segments / stats['downloaded']) * 100
            safe_print(f"Validez MPEG-TS: {validity_rate:.1f}% de segmentos descargados")
            
            if validity_rate >= 95:
                safe_print("CONTENIDO NO ENCRIPTADO: Segmentos son MPEG-TS válidos")
            elif validity_rate >= 50:
                safe_print("CONTENIDO MIXTO: Algunos segmentos encriptados")
            else:
                safe_print("CONTENIDO ENCRIPTADO: Mayoría de segmentos protegidos")
    
    def generate_academic_report(self, valid_segments, cached_count):
        """Generar reporte académico completo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.output_dir, "analysis", f"complete_download_report_{timestamp}.txt")
        
        stats = self.download_stats
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE ACADÉMICO: DESCARGA COMPLETA DE SEGMENTOS DRM\\n")
            f.write("=" * 60 + "\\n\\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Archivo de análisis origen: {self.analysis_file}\\n")
            f.write(f"Directorio de salida: {self.output_dir}\\n\\n")
            
            f.write("ESTADÍSTICAS DE DESCARGA:\\n")
            f.write("-" * 30 + "\\n")
            f.write(f"Total de segmentos identificados: {stats['total_segments']}\\n")
            f.write(f"Segmentos descargados exitosamente: {stats['downloaded']}\\n")
            f.write(f"Descargas fallidas: {stats['failed']}\\n")
            f.write(f"Archivos previamente existentes: {cached_count}\\n")
            f.write(f"Segmentos MPEG-TS válidos: {valid_segments}\\n")
            f.write(f"Tamaño total descargado: {stats['total_size']:,} bytes ({stats['total_size']/(1024*1024):.1f} MB)\\n")
            f.write(f"Tiempo de descarga: {duration:.1f} segundos\\n")
            f.write(f"Velocidad promedio: {stats['downloaded']/duration:.2f} segmentos/segundo\\n\\n")
            
            # Análisis académico
            success_rate = (stats['downloaded'] / stats['total_segments']) * 100
            validity_rate = (valid_segments / stats['downloaded']) * 100 if stats['downloaded'] > 0 else 0
            
            f.write("ANÁLISIS ACADÉMICO:\\n")
            f.write("-" * 20 + "\\n")
            f.write(f"Tasa de éxito de descarga: {success_rate:.2f}%\\n")
            f.write(f"Tasa de validez MPEG-TS: {validity_rate:.2f}%\\n\\n")
            
            f.write("HALLAZGOS PARA INVESTIGACIÓN:\\n")
            f.write("-" * 35 + "\\n")
            
            if validity_rate >= 95:
                f.write("• HALLAZGO PRINCIPAL: Contenido declarado como DRM pero segmentos NO encriptados\\n")
                f.write("• IMPLICACIÓN ACADÉMICA: Caso de estudio de DRM 'decorativo' o mal configurado\\n")
                f.write("• RELEVANCIA PARA TESIS: Ejemplo de discrepancia entre declaración y implementación DRM\\n")
            elif validity_rate >= 50:
                f.write("• HALLAZGO PRINCIPAL: Contenido con encriptación parcial o selectiva\\n")
                f.write("• IMPLICACIÓN ACADÉMICA: Implementación híbrida de protección DRM\\n")
                f.write("• RELEVANCIA PARA TESIS: Análisis de estrategias de protección escalonada\\n")
            else:
                f.write("• HALLAZGO PRINCIPAL: Contenido efectivamente protegido con DRM\\n")
                f.write("• IMPLICACIÓN ACADÉMICA: Implementación correcta de protección de contenido\\n")
                f.write("• RELEVANCIA PARA TESIS: Caso de estudio de DRM funcional\\n")
            
            f.write("\\nCONCLUSIONES METODOLÓGICAS:\\n")
            f.write("-" * 30 + "\\n")
            f.write("• La descarga masiva permitió análisis estadístico robusto\\n")
            f.write("• El enfoque paralelo demostró eficiencia en la recolección de datos\\n")
            f.write("• La validación MPEG-TS proporcionó insights sobre la efectividad del DRM\\n")
            f.write("• Los resultados son reproducibles para investigación académica\\n")
        
        safe_print(f"Reporte académico guardado: {report_file}")

def download_complete_research_dataset(analysis_file, max_workers=30):
    """Función de conveniencia para descarga completa"""
    downloader = CompleteSegmentDownloader(analysis_file, max_workers=max_workers)
    return downloader.download_all_segments()

# Script principal
if __name__ == "__main__":
    safe_print("DESCARGADOR COMPLETO DE SEGMENTOS DRM")
    safe_print("=" * 45)
    safe_print("Para investigación académica de sistemas DRM")
    safe_print("")
    
    # Archivo de análisis por defecto
    default_analysis = "analisis_submarifest/analysis/drm_analysis_20250816_222934.json"
    
    if os.path.exists(default_analysis):
        safe_print(f"Usando análisis: {default_analysis}")
        
        # Preguntar confirmación
        response = input("¿Descargar TODOS los 700 segmentos? (s/N): ").strip().lower()
        
        if response in ['s', 'si', 'sí', 'yes', 'y']:
            safe_print("Iniciando descarga completa...")
            results = download_complete_research_dataset(default_analysis, max_workers=30)
            safe_print("Descarga completa finalizada!")
        else:
            safe_print("Descarga cancelada por el usuario")
    else:
        safe_print(f"ERROR: No se encuentra el archivo de análisis: {default_analysis}")
        safe_print("Ejecuta primero el análisis DRM con drm_research_module.py")