#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Investigación DRM para Tesis Académica
===============================================

Este módulo está diseñado específicamente para investigación académica
y desarrollo de tesis sobre sistemas de gestión de derechos digitales (DRM).

Autor: Investigación Académica
Propósito: Análisis educativo de mecanismos DRM en contenido HLS
Uso: Solo para fines académicos y de investigación
"""

import requests
import re
import os
import struct
import tempfile
import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple
import logging

# Función segura para print con emojis en Windows
def safe_print(message):
    """Print seguro que maneja emojis en Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback para Windows con codificación problemática
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)

# Dependencias para criptografía (instalar con: pip install cryptography)
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    print("WARNING: Instalar cryptography: pip install cryptography")
    CRYPTO_AVAILABLE = False

class DRMResearchModule:
    """
    Módulo principal para investigación de DRM en contenido HLS
    
    Este módulo proporciona herramientas para analizar, estudiar y
    comprender los mecanismos de protección DRM en streaming de video.
    """
    
    def __init__(self, research_dir: str = "drm_research", thesis_mode: bool = True):
        self.thesis_mode = thesis_mode
        self.research_dir = research_dir
        self.session = requests.Session()
        self.setup_research_environment()
        self.analysis_log = []
        
        # Configurar logging para documentación académica
        self.setup_academic_logging()
        
        safe_print("🔬 [DRM RESEARCH] Módulo inicializado para investigación académica")
        safe_print(f"📁 Directorio de investigación: {self.research_dir}")
    
    def setup_research_environment(self):
        """Configura entorno de investigación"""
        # Crear directorio de investigación
        os.makedirs(self.research_dir, exist_ok=True)
        os.makedirs(os.path.join(self.research_dir, "segments"), exist_ok=True)
        os.makedirs(os.path.join(self.research_dir, "keys"), exist_ok=True)
        os.makedirs(os.path.join(self.research_dir, "decrypted"), exist_ok=True)
        os.makedirs(os.path.join(self.research_dir, "analysis"), exist_ok=True)
        
        # Headers realistas de navegador
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1'
        })
    
    def setup_academic_logging(self):
        """Configura logging académico detallado"""
        log_file = os.path.join(self.research_dir, f"research_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [DRM RESEARCH] - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_m3u8_drm(self, m3u8_url: str) -> Dict:
        """
        Análisis completo de DRM en manifest M3U8
        
        Args:
            m3u8_url (str): URL del manifest M3U8 a analizar
            
        Returns:
            Dict: Resultados completos del análisis académico
        """
        self.logger.info(f"Iniciando análisis DRM de: {m3u8_url}")
        
        analysis_results = {
            'url': m3u8_url,
            'timestamp': datetime.now().isoformat(),
            'manifest_info': {},
            'encryption_analysis': {},
            'key_analysis': {},
            'segment_analysis': {},
            'decryption_attempts': {},
            'academic_findings': [],
            'success': False
        }
        
        try:
            # 1. Analizar manifest
            analysis_results['manifest_info'] = self.analyze_manifest(m3u8_url)
            
            # 2. Analizar encriptación
            analysis_results['encryption_analysis'] = self.analyze_encryption_methods(
                analysis_results['manifest_info']
            )
            
            # 3. Obtener y analizar claves
            analysis_results['key_analysis'] = self.analyze_encryption_keys(
                analysis_results['encryption_analysis']
            )
            
            # 4. Analizar segmentos
            analysis_results['segment_analysis'] = self.analyze_encrypted_segments(
                analysis_results['manifest_info'], 
                analysis_results['key_analysis']
            )
            
            # 5. Intentar descifrado académico
            if CRYPTO_AVAILABLE and analysis_results['key_analysis']['keys_obtained']:
                analysis_results['decryption_attempts'] = self.attempt_academic_decryption(
                    analysis_results['key_analysis'],
                    analysis_results['segment_analysis']
                )
            
            # 6. Generar hallazgos académicos
            analysis_results['academic_findings'] = self.generate_academic_findings(analysis_results)
            analysis_results['success'] = True
            
            # 7. Documentar resultados
            self.document_analysis_results(analysis_results)
            
        except Exception as e:
            self.logger.error(f"Error en análisis DRM: {e}")
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    def analyze_manifest(self, m3u8_url: str) -> Dict:
        """Analiza el manifest M3U8 en detalle"""
        self.logger.info("Analizando estructura del manifest M3U8")
        
        response = self.session.get(m3u8_url)
        response.raise_for_status()
        
        manifest_content = response.text
        
        manifest_info = {
            'url': m3u8_url,
            'content_length': len(manifest_content),
            'is_master_playlist': '#EXT-X-STREAM-INF' in manifest_content,
            'has_encryption': '#EXT-X-KEY' in manifest_content,
            'segments': [],
            'encryption_keys': [],
            'raw_content': manifest_content
        }
        
        # Extraer segmentos
        segment_pattern = r'([^\n]+\.ts[^\n]*)'
        segments = re.findall(segment_pattern, manifest_content)
        
        for segment in segments:
            segment_url = urljoin(m3u8_url, segment.strip())
            manifest_info['segments'].append(segment_url)
        
        # Extraer información de claves de encriptación
        key_pattern = r'#EXT-X-KEY:([^\n]+)'
        key_lines = re.findall(key_pattern, manifest_content)
        
        for key_line in key_lines:
            key_info = self.parse_encryption_key_line(key_line, m3u8_url)
            manifest_info['encryption_keys'].append(key_info)
        
        self.logger.info(f"Manifest analizado: {len(segments)} segmentos, {len(key_lines)} claves")
        
        return manifest_info
    
    def parse_encryption_key_line(self, key_line: str, base_url: str) -> Dict:
        """Parsea línea EXT-X-KEY para extraer información de encriptación"""
        key_info = {
            'raw_line': key_line,
            'method': None,
            'uri': None,
            'iv': None,
            'key_format': None,
            'key_format_versions': None
        }
        
        # Extraer método de encriptación
        method_match = re.search(r'METHOD=([^,\s]+)', key_line)
        if method_match:
            key_info['method'] = method_match.group(1)
        
        # Extraer URI de la clave
        uri_match = re.search(r'URI="([^"]+)"', key_line)
        if uri_match:
            key_info['uri'] = urljoin(base_url, uri_match.group(1))
        
        # Extraer IV (Initialization Vector)
        iv_match = re.search(r'IV=0x([0-9A-Fa-f]+)', key_line)
        if iv_match:
            key_info['iv'] = iv_match.group(1)
            key_info['iv_bytes'] = bytes.fromhex(iv_match.group(1))
        
        # Extraer formato de clave
        format_match = re.search(r'KEYFORMAT="([^"]+)"', key_line)
        if format_match:
            key_info['key_format'] = format_match.group(1)
        
        return key_info
    
    def analyze_encryption_methods(self, manifest_info: Dict) -> Dict:
        """Analiza métodos de encriptación utilizados"""
        self.logger.info("Analizando métodos de encriptación")
        
        encryption_analysis = {
            'methods_detected': [],
            'complexity_level': 'NONE',
            'drm_type': 'NONE',
            'academic_classification': []
        }
        
        for key_info in manifest_info['encryption_keys']:
            method = key_info['method']
            if method and method not in encryption_analysis['methods_detected']:
                encryption_analysis['methods_detected'].append(method)
        
        # Clasificar complejidad académica
        if 'AES-128' in encryption_analysis['methods_detected']:
            encryption_analysis['complexity_level'] = 'BASIC'
            encryption_analysis['drm_type'] = 'AES_STANDARD'
            encryption_analysis['academic_classification'].append('Encriptación AES-128 estándar')
        
        if 'SAMPLE-AES' in encryption_analysis['methods_detected']:
            encryption_analysis['complexity_level'] = 'INTERMEDIATE'
            encryption_analysis['drm_type'] = 'SAMPLE_AES'
            encryption_analysis['academic_classification'].append('Encriptación SAMPLE-AES (parcial)')
        
        if any('ISO-23001-7' in str(key) for key in manifest_info['encryption_keys']):
            encryption_analysis['complexity_level'] = 'ADVANCED'
            encryption_analysis['drm_type'] = 'COMMON_ENCRYPTION'
            encryption_analysis['academic_classification'].append('Common Encryption (CENC)')
        
        return encryption_analysis
    
    def analyze_encryption_keys(self, encryption_analysis: Dict) -> Dict:
        """Obtiene y analiza claves de encriptación"""
        self.logger.info("Obteniendo claves de encriptación para análisis")
        
        key_analysis = {
            'keys_obtained': 0,
            'keys_failed': 0,
            'key_data': {},
            'key_characteristics': [],
            'academic_notes': []
        }
        
        # Esta sección requiere análisis específico según el tipo de DRM
        # Por ahora documentamos la estructura para investigación académica
        
        key_analysis['academic_notes'].append("Análisis de claves requiere implementación específica por tipo de DRM")
        key_analysis['academic_notes'].append("Para AES-128: Las claves pueden obtenerse directamente del servidor")
        key_analysis['academic_notes'].append("Para Widevine/PlayReady: Requiere CDM y certificados válidos")
        
        return key_analysis
    
    def analyze_encrypted_segments(self, manifest_info: Dict, key_analysis: Dict) -> Dict:
        """Analiza segmentos encriptados"""
        self.logger.info("Analizando segmentos encriptados")
        
        segment_analysis = {
            'total_segments': len(manifest_info['segments']),
            'segments_analyzed': 0,
            'encryption_patterns': [],
            'segment_characteristics': {},
            'academic_observations': []
        }
        
        # Analizar algunos segmentos para investigación
        max_segments_to_analyze = min(5, len(manifest_info['segments']))
        
        for i, segment_url in enumerate(manifest_info['segments'][:max_segments_to_analyze]):
            try:
                self.logger.info(f"Analizando segmento {i+1}/{max_segments_to_analyze}")
                
                response = self.session.get(segment_url)
                if response.status_code == 200:
                    segment_data = response.content
                    
                    # Análisis de características del segmento
                    characteristics = {
                        'size': len(segment_data),
                        'first_bytes': segment_data[:16].hex() if len(segment_data) >= 16 else '',
                        'has_sync_byte': segment_data[0] == 0x47 if len(segment_data) > 0 else False,
                        'appears_encrypted': not (segment_data[0] == 0x47 if len(segment_data) > 0 else False)
                    }
                    
                    segment_analysis['segment_characteristics'][f'segment_{i}'] = characteristics
                    segment_analysis['segments_analyzed'] += 1
                    
                    # Guardar segmento para análisis posterior
                    segment_file = os.path.join(self.research_dir, "segments", f"segment_{i:03d}.ts")
                    with open(segment_file, 'wb') as f:
                        f.write(segment_data)
                    
            except Exception as e:
                self.logger.error(f"Error analizando segmento {i}: {e}")
        
        # Generar observaciones académicas
        encrypted_count = sum(1 for char in segment_analysis['segment_characteristics'].values() 
                             if char.get('appears_encrypted', False))
        
        segment_analysis['academic_observations'].append(
            f"De {segment_analysis['segments_analyzed']} segmentos analizados, "
            f"{encrypted_count} parecen estar encriptados"
        )
        
        return segment_analysis
    
    def attempt_academic_decryption(self, key_analysis: Dict, segment_analysis: Dict) -> Dict:
        """Intenta descifrado para investigación académica"""
        self.logger.info("Iniciando intentos de descifrado académico")
        
        decryption_results = {
            'methods_attempted': [],
            'successful_decryptions': 0,
            'failed_attempts': 0,
            'academic_findings': [],
            'decrypted_files': []
        }
        
        # Por ahora, documentar la metodología para la tesis
        decryption_results['academic_findings'].append(
            "El descifrado de contenido DRM requiere:"
        )
        decryption_results['academic_findings'].append(
            "1. Obtención de claves de descifrado válidas"
        )
        decryption_results['academic_findings'].append(
            "2. Conocimiento del algoritmo de encriptación específico"
        )
        decryption_results['academic_findings'].append(
            "3. Vectores de inicialización (IV) correctos"
        )
        decryption_results['academic_findings'].append(
            "4. Cumplimiento de requisitos de hardware/software del CDM"
        )
        
        return decryption_results
    
    def generate_academic_findings(self, analysis_results: Dict) -> List[str]:
        """Genera hallazgos académicos para la tesis"""
        findings = []
        
        findings.append("=== HALLAZGOS ACADÉMICOS PARA TESIS ===")
        
        # Análisis de complejidad DRM
        complexity = analysis_results['encryption_analysis'].get('complexity_level', 'NONE')
        findings.append(f"Nivel de complejidad DRM detectado: {complexity}")
        
        # Métodos de encriptación
        methods = analysis_results['encryption_analysis'].get('methods_detected', [])
        if methods:
            findings.append(f"Métodos de encriptación identificados: {', '.join(methods)}")
        
        # Análisis de segmentos
        total_segments = analysis_results['segment_analysis'].get('total_segments', 0)
        analyzed_segments = analysis_results['segment_analysis'].get('segments_analyzed', 0)
        findings.append(f"Segmentos analizados: {analyzed_segments} de {total_segments} totales")
        
        # Recomendaciones para la tesis
        findings.append("=== RECOMENDACIONES PARA INVESTIGACIÓN ===")
        findings.append("1. Ampliar análisis a diferentes tipos de contenido DRM")
        findings.append("2. Estudiar variaciones en implementaciones de CDM")
        findings.append("3. Documentar diferencias entre plataformas de streaming")
        findings.append("4. Analizar impacto en experiencia de usuario")
        
        return findings
    
    def document_analysis_results(self, analysis_results: Dict):
        """Documenta resultados para la tesis"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Guardar análisis completo
        results_file = os.path.join(self.research_dir, "analysis", f"drm_analysis_{timestamp}.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Generar reporte académico
        report_file = os.path.join(self.research_dir, "analysis", f"academic_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE ACADÉMICO DE ANÁLISIS DRM\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"URL Analizada: {analysis_results['url']}\n")
            f.write(f"Timestamp: {analysis_results['timestamp']}\n\n")
            
            f.write("HALLAZGOS ACADÉMICOS:\n")
            f.write("-" * 25 + "\n")
            for finding in analysis_results.get('academic_findings', []):
                f.write(f"• {finding}\n")
        
        self.logger.info(f"Resultados documentados en: {results_file}")
        self.logger.info(f"Reporte académico en: {report_file}")

# === FUNCIONES DE UTILIDAD ===

def create_research_session(research_dir: str = "drm_research") -> DRMResearchModule:
    """Crea nueva sesión de investigación DRM"""
    return DRMResearchModule(research_dir=research_dir, thesis_mode=True)

def analyze_drm_content(m3u8_url: str, research_dir: str = "drm_research") -> Dict:
    """Función de conveniencia para análisis rápido"""
    module = create_research_session(research_dir)
    return module.analyze_m3u8_drm(m3u8_url)

# === EJEMPLO DE USO ===
if __name__ == "__main__":
    print("🔬 Módulo de Investigación DRM para Tesis")
    print("=" * 40)
    
    # Ejemplo de uso del módulo
    # research_module = create_research_session("mi_investigacion_drm")
    # results = research_module.analyze_m3u8_drm("https://ejemplo.com/video.m3u8")
    # print(f"Análisis completado. Resultados: {results['success']}")
    
    print("📚 Para usar este módulo en tu tesis:")
    print("1. from drm_research_module import create_research_session")
    print("2. module = create_research_session('mi_investigacion')")
    print("3. results = module.analyze_m3u8_drm('URL_DE_TU_CONTENIDO')")
    print("4. Revisa los archivos generados en el directorio de investigación")