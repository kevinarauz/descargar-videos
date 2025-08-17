#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Descifrado DRM para Investigación Académica
===================================================

AVISO IMPORTANTE: Este módulo está destinado EXCLUSIVAMENTE para:
- Investigación académica y educativa
- Desarrollo de tesis universitarias  
- Análisis de seguridad en entornos controlados
- Estudio de protocolos DRM con contenido propio

NO para uso comercial o distribución no autorizada.
"""

import os
import json
import struct
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Funciones de criptografía
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    print("ADVERTENCIA: Instalar cryptography para descifrado: pip install cryptography")
    CRYPTO_AVAILABLE = False

def safe_print(message):
    """Print seguro para Windows"""
    try:
        print(message)
    except UnicodeEncodeError:
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        print(safe_message)

class DRMDecryptionModule:
    """
    Módulo académico para descifrado de contenido DRM AES-128
    
    IMPORTANTE: Solo para investigación educativa
    """
    
    def __init__(self, analysis_file: str, output_dir: str = "decrypted_content"):
        self.analysis_file = analysis_file
        self.output_dir = output_dir
        self.session = requests.Session()
        self.decryption_stats = {
            'total_segments': 0,
            'encrypted_segments': 0,
            'decrypted_successfully': 0,
            'decryption_failed': 0,
            'keys_obtained': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Headers realistas
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        })
        
        self.setup_output_directory()
        safe_print("MÓDULO DE DESCIFRADO DRM - INVESTIGACIÓN ACADÉMICA")
        safe_print("=" * 55)
    
    def setup_output_directory(self):
        """Configurar directorios de salida"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "decrypted_segments"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "original_segments"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "keys"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "analysis"), exist_ok=True)
    
    def load_drm_analysis(self) -> Dict:
        """Cargar análisis DRM previo"""
        safe_print(f"Cargando análisis DRM: {self.analysis_file}")
        
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        manifest_info = data['manifest_info']
        encryption_keys = manifest_info.get('encryption_keys', [])
        segments = manifest_info.get('segments', [])
        
        safe_print(f"Segmentos encontrados: {len(segments)}")
        safe_print(f"Claves de encriptación: {len(encryption_keys)}")
        
        return data
    
    def obtain_decryption_keys(self, encryption_keys: List[Dict]) -> Dict[str, bytes]:
        """Obtener claves de descifrado del servidor"""
        safe_print("OBTENIENDO CLAVES DE DESCIFRADO")
        safe_print("-" * 35)
        
        obtained_keys = {}
        
        for i, key_info in enumerate(encryption_keys):
            method = key_info.get('method')
            key_uri = key_info.get('uri')
            
            if method == 'AES-128' and key_uri:
                safe_print(f"Descargando clave AES-128 #{i+1}: {key_uri}")
                
                try:
                    # Obtener clave del servidor
                    response = self.session.get(key_uri, timeout=30)
                    response.raise_for_status()
                    
                    key_data = response.content
                    
                    # Validar longitud de clave AES-128 (16 bytes)
                    if len(key_data) == 16:
                        obtained_keys[key_uri] = key_data
                        self.decryption_stats['keys_obtained'] += 1
                        
                        # Guardar clave para análisis
                        key_file = os.path.join(self.output_dir, "keys", f"key_{i:02d}.key")
                        with open(key_file, 'wb') as f:
                            f.write(key_data)
                        
                        safe_print(f"✅ Clave obtenida: {len(key_data)} bytes")
                        safe_print(f"   Guardada en: {key_file}")
                        safe_print(f"   Hex: {key_data.hex()}")
                    else:
                        safe_print(f"❌ Clave inválida: {len(key_data)} bytes (esperado: 16)")
                        
                except Exception as e:
                    safe_print(f"❌ Error obteniendo clave: {e}")
        
        safe_print(f"\nClaves AES-128 obtenidas: {len(obtained_keys)}")
        return obtained_keys
    
    def decrypt_aes128_segment(self, encrypted_data: bytes, key: bytes, 
                              segment_index: int, iv: Optional[bytes] = None) -> Optional[bytes]:
        """
        Descifrar segmento individual con AES-128-CBC
        
        Args:
            encrypted_data: Datos encriptados del segmento
            key: Clave AES de 16 bytes
            segment_index: Índice del segmento para generar IV
            iv: Vector de inicialización opcional
            
        Returns:
            Datos descifrados o None si falla
        """
        if not CRYPTO_AVAILABLE:
            safe_print("❌ Librería cryptography no disponible")
            return None
        
        try:
            # Generar IV si no se proporciona
            if iv is None:
                # HLS estándar: IV = segment_index como entero de 16 bytes
                iv = struct.pack('>4I', 0, 0, 0, segment_index)
            
            # Verificar longitudes
            if len(key) != 16:
                safe_print(f"❌ Clave inválida: {len(key)} bytes (necesario: 16)")
                return None
            
            if len(iv) != 16:
                safe_print(f"❌ IV inválido: {len(iv)} bytes (necesario: 16)")
                return None
            
            # Crear cipher AES-128-CBC
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Descifrar datos
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Validar resultado: debe comenzar con sync byte MPEG-TS (0x47)
            if len(decrypted_data) > 0 and decrypted_data[0] == 0x47:
                return decrypted_data
            else:
                # Intentar sin padding si el primer intento falla
                safe_print(f"⚠️ Segmento {segment_index}: No tiene sync byte MPEG-TS tras descifrado")
                return decrypted_data  # Devolver de todos modos para análisis
            
        except Exception as e:
            safe_print(f"❌ Error descifrando segmento {segment_index}: {e}")
            return None
    
    def process_segment_with_decryption(self, segment_info: Tuple[int, str], 
                                      decryption_keys: Dict[str, bytes]) -> Dict:
        """Procesar un segmento: descargar, descifrar y validar"""
        segment_index, segment_url = segment_info
        
        result = {
            'index': segment_index,
            'url': segment_url,
            'downloaded': False,
            'encrypted': False,
            'decrypted': False,
            'valid_ts': False,
            'file_size': 0,
            'error': None
        }
        
        try:
            # Descargar segmento original
            response = self.session.get(segment_url, timeout=30)
            response.raise_for_status()
            
            original_data = response.content
            result['downloaded'] = True
            result['file_size'] = len(original_data)
            
            # Guardar segmento original
            original_file = os.path.join(self.output_dir, "original_segments", 
                                       f"original_{segment_index:04d}.ts")
            with open(original_file, 'wb') as f:
                f.write(original_data)
            
            # Verificar si está encriptado (no tiene sync byte 0x47)
            is_encrypted = len(original_data) == 0 or original_data[0] != 0x47
            result['encrypted'] = is_encrypted
            
            if is_encrypted and decryption_keys:
                # Intentar descifrado con cada clave disponible
                for key_uri, key_data in decryption_keys.items():
                    decrypted_data = self.decrypt_aes128_segment(
                        original_data, key_data, segment_index
                    )
                    
                    if decrypted_data:
                        # Guardar segmento descifrado
                        decrypted_file = os.path.join(self.output_dir, "decrypted_segments",
                                                    f"decrypted_{segment_index:04d}.ts")
                        with open(decrypted_file, 'wb') as f:
                            f.write(decrypted_data)
                        
                        result['decrypted'] = True
                        
                        # Validar como MPEG-TS
                        if len(decrypted_data) > 0 and decrypted_data[0] == 0x47:
                            result['valid_ts'] = True
                        
                        break  # Éxito con esta clave
            
            elif not is_encrypted:
                # Segmento ya descifrado, copiarlo
                decrypted_file = os.path.join(self.output_dir, "decrypted_segments",
                                            f"decrypted_{segment_index:04d}.ts")
                with open(decrypted_file, 'wb') as f:
                    f.write(original_data)
                
                result['decrypted'] = True
                result['valid_ts'] = True
        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def decrypt_all_segments(self, max_workers: int = 20) -> Dict:
        """Descifrar todos los segmentos del contenido"""
        safe_print("INICIANDO DESCIFRADO COMPLETO DE CONTENIDO DRM")
        safe_print("=" * 50)
        
        # Cargar análisis
        drm_data = self.load_drm_analysis()
        manifest_info = drm_data['manifest_info']
        
        # Obtener claves de descifrado
        encryption_keys = manifest_info.get('encryption_keys', [])
        decryption_keys = self.obtain_decryption_keys(encryption_keys)
        
        if not decryption_keys:
            safe_print("❌ No se pudieron obtener claves de descifrado")
            return {'success': False, 'error': 'No decryption keys available'}
        
        # Preparar segmentos para procesamiento
        segments = manifest_info.get('segments', [])
        segment_data = [(i, url) for i, url in enumerate(segments)]
        
        self.decryption_stats['total_segments'] = len(segments)
        self.decryption_stats['start_time'] = datetime.now()
        
        # Contadores
        results = []
        
        safe_print(f"\nProcesando {len(segments)} segmentos con {max_workers} workers...")
        safe_print(f"Claves disponibles: {len(decryption_keys)}")
        safe_print("")
        
        # Procesamiento paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_segment_with_decryption, 
                                     seg_info, decryption_keys): seg_info 
                      for seg_info in segment_data}
            
            # Procesar con barra de progreso
            with tqdm(total=len(segments), desc="Descifrando segmentos", unit="seg") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
                    
                    # Actualizar estadísticas
                    if result['encrypted']:
                        self.decryption_stats['encrypted_segments'] += 1
                    
                    if result['decrypted'] and result['valid_ts']:
                        self.decryption_stats['decrypted_successfully'] += 1
                    elif result['encrypted'] and not result['decrypted']:
                        self.decryption_stats['decryption_failed'] += 1
                    
                    # Actualizar descripción
                    desc = f"Descifrados: {self.decryption_stats['decrypted_successfully']}, " \
                           f"Fallos: {self.decryption_stats['decryption_failed']}"
                    pbar.set_description(desc)
                    pbar.update(1)
        
        # Finalizar
        self.decryption_stats['end_time'] = datetime.now()
        
        # Generar reporte
        self.generate_decryption_report(results)
        
        return {
            'success': True,
            'stats': self.decryption_stats,
            'results': results
        }
    
    def generate_decryption_report(self, results: List[Dict]):
        """Generar reporte académico del descifrado"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.output_dir, "analysis", 
                                 f"decryption_report_{timestamp}.txt")
        
        stats = self.decryption_stats
        duration = (stats['end_time'] - stats['start_time']).total_seconds()
        
        # Mostrar estadísticas en consola
        safe_print("\nRESULTADOS DEL DESCIFRADO DRM")
        safe_print("=" * 35)
        safe_print(f"Total de segmentos: {stats['total_segments']}")
        safe_print(f"Segmentos encriptados: {stats['encrypted_segments']}")
        safe_print(f"Descifrados exitosamente: {stats['decrypted_successfully']}")
        safe_print(f"Fallos de descifrado: {stats['decryption_failed']}")
        safe_print(f"Claves obtenidas: {stats['keys_obtained']}")
        safe_print(f"Tiempo total: {duration:.1f} segundos")
        
        # Calcular tasas
        encryption_rate = (stats['encrypted_segments'] / stats['total_segments']) * 100
        success_rate = (stats['decrypted_successfully'] / stats['encrypted_segments']) * 100 \
                      if stats['encrypted_segments'] > 0 else 0
        
        safe_print(f"Tasa de encriptación: {encryption_rate:.1f}%")
        safe_print(f"Tasa de descifrado exitoso: {success_rate:.1f}%")
        
        # Evaluación académica
        safe_print("\nEVALUACIÓN ACADÉMICA:")
        safe_print("-" * 20)
        
        if success_rate >= 95:
            safe_print("EXCELENTE: Descifrado casi completo - DRM crackeado")
        elif success_rate >= 80:
            safe_print("BUENA: Mayoría de contenido descifrado")
        elif success_rate >= 50:
            safe_print("PARCIAL: Descifrado limitado, revisar claves/algoritmo")
        else:
            safe_print("LIMITADO: DRM resistente al descifrado")
        
        # Generar archivo de reporte
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE ACADÉMICO: DESCIFRADO DE CONTENIDO DRM\\n")
            f.write("=" * 55 + "\\n\\n")
            
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Propósito: Investigación académica de descifrado DRM\\n")
            f.write(f"Archivo fuente: {self.analysis_file}\\n\\n")
            
            f.write("ESTADÍSTICAS DE DESCIFRADO:\\n")
            f.write("-" * 30 + "\\n")
            f.write(f"Total de segmentos procesados: {stats['total_segments']}\\n")
            f.write(f"Segmentos identificados como encriptados: {stats['encrypted_segments']}\\n")
            f.write(f"Segmentos descifrados exitosamente: {stats['decrypted_successfully']}\\n")
            f.write(f"Fallos en descifrado: {stats['decryption_failed']}\\n")
            f.write(f"Claves AES-128 obtenidas: {stats['keys_obtained']}\\n")
            f.write(f"Tiempo de procesamiento: {duration:.2f} segundos\\n\\n")
            
            f.write("MÉTRICAS ACADÉMICAS:\\n")
            f.write("-" * 20 + "\\n")
            f.write(f"Tasa de encriptación: {encryption_rate:.2f}%\\n")
            f.write(f"Tasa de descifrado exitoso: {success_rate:.2f}%\\n\\n")
            
            f.write("ANÁLISIS PARA TESIS:\\n")
            f.write("-" * 20 + "\\n")
            
            if success_rate >= 95:
                f.write("• HALLAZGO: DRM AES-128 completamente vulnerable al descifrado\\n")
                f.write("• IMPLICACIÓN: Las claves son accesibles y el algoritmo es reversible\\n")
                f.write("• RELEVANCIA: Demuestra limitaciones de DRM básico en HLS\\n")
            elif success_rate >= 50:
                f.write("• HALLAZGO: DRM parcialmente vulnerable, algunos segmentos resistentes\\n")
                f.write("• IMPLICACIÓN: Implementación inconsistente o claves múltiples\\n")
                f.write("• RELEVANCIA: Caso de estudio de protección híbrida\\n")
            else:
                f.write("• HALLAZGO: DRM resistente al descifrado académico\\n")
                f.write("• IMPLICACIÓN: Protección efectiva o algoritmo complejo\\n")
                f.write("• RELEVANCIA: Límites de técnicas de descifrado estudiadas\\n")
        
        safe_print(f"Reporte guardado: {report_file}")

def decrypt_drm_content(analysis_file: str, max_workers: int = 20) -> Dict:
    """Función de conveniencia para descifrado completo"""
    decryptor = DRMDecryptionModule(analysis_file)
    return decryptor.decrypt_all_segments(max_workers)

# Script principal
if __name__ == "__main__":
    safe_print("DESCIFRADOR DRM - INVESTIGACIÓN ACADÉMICA")
    safe_print("=" * 45)
    safe_print("AVISO: Solo para uso educativo y de investigación")
    safe_print("")
    
    # Archivo de análisis por defecto
    default_analysis = "analisis_submarifest/analysis/drm_analysis_20250816_222934.json"
    
    if os.path.exists(default_analysis):
        safe_print(f"Usando análisis: {default_analysis}")
        safe_print("INICIANDO DESCIFRADO DE CONTENIDO DRM...")
        safe_print("")
        
        results = decrypt_drm_content(default_analysis, max_workers=20)
        
        if results['success']:
            safe_print("\\n🎉 DESCIFRADO COMPLETADO")
            safe_print("Revisa el directorio decrypted_content/ para los resultados")
        else:
            safe_print("❌ Error en descifrado")
    else:
        safe_print(f"ERROR: Archivo de análisis no encontrado: {default_analysis}")
        safe_print("Ejecuta primero el análisis DRM")