#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Descifrado AES-128 para Contenido HLS Disfrazado
=========================================================

Este módulo maneja el descifrado de segmentos HLS que están:
1. Encriptados con AES-128 
2. Disfrazados como imágenes (extensiones .jpg/.png)
3. Requieren claves de descifrado específicas

Autor: Sistema M3U8 Downloader
Propósito: Descifrado de contenido multimedia académico
"""

import os
import struct
import requests
import urllib3
from typing import Dict, List, Optional, Tuple, Callable
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import logging

# Suprimir warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AESDecryptor:
    """Descifrador AES-128 especializado para contenido HLS disfrazado"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.verify = False
        
        # Cache de claves descargadas
        self.key_cache = {}
    
    def decrypt_disguised_segments(self, 
                                 segments: List[str], 
                                 encryption_keys: List[Dict],
                                 output_dir: str,
                                 progress_callback: Optional[Callable] = None) -> Dict:
        """
        Descifra segmentos disfrazados con AES-128
        
        Args:
            segments (List[str]): URLs de segmentos a descifrar
            encryption_keys (List[Dict]): Información de claves de encriptación
            output_dir (str): Directorio donde guardar segmentos descifrados
            progress_callback (Callable): Función de callback para reportar progreso
            
        Returns:
            Dict: Resultados del proceso de descifrado
        """
        results = {
            'total_segments': len(segments),
            'decrypted_segments': 0,
            'failed_segments': 0,
            'skipped_segments': 0,
            'decrypted_files': [],
            'errors': [],
            'keys_used': []
        }
        
        # Crear directorio de salida
        os.makedirs(output_dir, exist_ok=True)
        
        # Obtener claves de descifrado
        decryption_keys = self._get_decryption_keys(encryption_keys)
        results['keys_used'] = list(decryption_keys.keys())
        
        if not decryption_keys:
            results['errors'].append("No se pudieron obtener las claves de descifrado")
            return results
        
        # Procesar cada segmento
        for i, segment_url in enumerate(segments):
            try:
                if progress_callback:
                    progress_callback({
                        'segment_index': i,
                        'total_segments': len(segments),
                        'status': 'downloading',
                        'url': segment_url
                    })
                
                # Descargar segmento encriptado
                encrypted_data = self._download_segment(segment_url)
                if not encrypted_data:
                    results['failed_segments'] += 1
                    results['errors'].append(f"Fallo al descargar segmento {i}: {segment_url}")
                    continue
                
                # Probar descifrado con múltiples claves si es necesario
                decrypted_data = None
                key_attempts = 0
                
                # Primero intentar con la clave seleccionada por estrategia
                primary_key = self._select_decryption_key(decryption_keys, i)
                if primary_key:
                    decrypted_data = self._decrypt_segment_aes128(encrypted_data, primary_key, i)
                    key_attempts += 1
                
                # Si falló, probar con todas las claves disponibles
                if not decrypted_data and len(decryption_keys) > 1:
                    for key_url, key_data in decryption_keys.items():
                        if key_data != primary_key:  # No repetir la clave ya probada
                            decrypted_data = self._decrypt_segment_aes128(encrypted_data, key_data, i)
                            key_attempts += 1
                            if decrypted_data:
                                self.logger.info(f"🔑 Segmento {i}: Descifrado exitoso con clave alternativa ({key_url})")
                                break
                
                if not decrypted_data:
                    results['failed_segments'] += 1
                    results['errors'].append(f"Segmento {i}: Falló con {key_attempts} claves y {5} estrategias IV")
                    continue
                
                # Guardar segmento descifrado
                output_file = os.path.join(output_dir, f"segment_{i:05d}.ts")
                with open(output_file, 'wb') as f:
                    f.write(decrypted_data)
                
                results['decrypted_files'].append(output_file)
                results['decrypted_segments'] += 1
                
                if progress_callback:
                    progress_callback({
                        'segment_index': i,
                        'total_segments': len(segments),
                        'status': 'decrypted',
                        'output_file': output_file
                    })
                    
            except Exception as e:
                results['failed_segments'] += 1
                results['errors'].append(f"Error procesando segmento {i}: {str(e)}")
                self.logger.error(f"Error en segmento {i}: {e}")
        
        self.logger.info(f"Descifrado completo: {results['decrypted_segments']}/{results['total_segments']} exitosos")
        return results
    
    def _get_decryption_keys(self, encryption_keys: List[Dict]) -> Dict[str, bytes]:
        """Obtiene y descarga las claves de descifrado"""
        keys = {}
        
        for key_info in encryption_keys:
            key_uri = key_info.get('uri')
            key_method = key_info.get('method')
            
            if not key_uri or key_method != 'AES-128':
                continue
            
            # Verificar cache
            if key_uri in self.key_cache:
                keys[key_uri] = self.key_cache[key_uri]
                continue
            
            try:
                # Descargar clave
                response = self.session.get(key_uri, timeout=10)
                if response.status_code == 200:
                    key_data = response.content
                    if len(key_data) == 16:  # Clave AES-128 debe ser de 16 bytes
                        keys[key_uri] = key_data
                        self.key_cache[key_uri] = key_data
                        self.logger.info(f"Clave obtenida: {key_uri}")
                    else:
                        self.logger.warning(f"Clave de tamaño incorrecto: {len(key_data)} bytes")
                else:
                    self.logger.error(f"Error descargando clave {key_uri}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Error obteniendo clave {key_uri}: {e}")
        
        return keys
    
    def _download_segment(self, segment_url: str) -> Optional[bytes]:
        """Descarga un segmento encriptado"""
        try:
            response = self.session.get(segment_url, timeout=15)
            if response.status_code == 200:
                return response.content
            else:
                self.logger.error(f"Error descargando segmento: HTTP {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error descargando segmento {segment_url}: {e}")
            return None
    
    def _select_decryption_key(self, keys: Dict[str, bytes], segment_index: int) -> Optional[bytes]:
        """Selecciona la clave apropiada para un segmento con rotación inteligente"""
        if not keys:
            return None
        
        key_list = list(keys.values())
        
        # Si solo hay una clave, usarla
        if len(key_list) == 1:
            return key_list[0]
        
        # Si hay múltiples claves, probar estrategias de rotación
        if len(key_list) >= 2:
            # Estrategia 1: Alternar claves cada cierto número de segmentos
            # Muchos streams HLS cambian de clave cada 10-50 segmentos
            if segment_index < 10:
                # Usar primera clave para los primeros segmentos
                return key_list[0]
            else:
                # Alternar entre claves basado en grupos
                key_group = (segment_index // 50) % len(key_list)
                return key_list[key_group]
        
        return key_list[0]
    
    def _decrypt_segment_aes128(self, encrypted_data: bytes, key: bytes, segment_index: int) -> Optional[bytes]:
        """Descifra un segmento usando AES-128 con múltiples estrategias de IV"""
        try:
            # Lista de estrategias de IV para probar
            iv_strategies = [
                # Estrategia 1: IV basado en índice (HLS estándar)
                struct.pack('>16B', *([0] * 15 + [segment_index & 0xFF])),
                
                # Estrategia 2: IV basado en índice con formato largo
                struct.pack('>Q', segment_index) + b'\x00' * 8,
                
                # Estrategia 3: IV zero (streams simples)
                b'\x00' * 16,
                
                # Estrategia 4: IV con índice en formato little-endian
                struct.pack('<Q', segment_index) + b'\x00' * 8,
                
                # Estrategia 5: IV con índice en los primeros 4 bytes
                struct.pack('>I', segment_index) + b'\x00' * 12
            ]
            
            for strategy_num, iv in enumerate(iv_strategies):
                try:
                    # Crear cipher AES-128-CBC
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    
                    # Descifrar datos
                    decrypted_data = cipher.decrypt(encrypted_data)
                    
                    # Intentar remover padding PKCS7
                    try:
                        unpadded_data = unpad(decrypted_data, AES.block_size)
                        # Si el unpad funciona, usar los datos sin padding
                        test_data = unpadded_data
                    except ValueError:
                        # Si falla el unpad, usar datos originales
                        test_data = decrypted_data
                    
                    # Verificar que el resultado sea un segmento TS válido
                    if len(test_data) > 4:
                        # Buscar sync byte en las primeras posiciones
                        for offset in range(min(16, len(test_data))):
                            if test_data[offset] == 0x47:
                                self.logger.info(f"✅ Segmento {segment_index} descifrado con estrategia IV {strategy_num + 1}, sync byte en offset {offset}")
                                # Si encontramos sync byte con offset, ajustar los datos
                                if offset > 0:
                                    return test_data[offset:]
                                else:
                                    return test_data
                        
                        # Si no encontramos sync byte, verificar si son datos válidos por entropía
                        if self._appears_valid_ts_content(test_data):
                            self.logger.info(f"✅ Segmento {segment_index} descifrado con estrategia IV {strategy_num + 1} (contenido válido sin sync byte)")
                            return test_data
                    
                except Exception as cipher_error:
                    continue  # Probar siguiente estrategia
            
            # Si todas las estrategias fallaron, devolver datos originales para debug
            self.logger.warning(f"❌ Segmento {segment_index}: Todas las estrategias IV fallaron")
            return None
                    
        except Exception as e:
            self.logger.error(f"❌ Error crítico descifrando segmento {segment_index}: {e}")
            return None
    
    def _appears_valid_ts_content(self, data: bytes) -> bool:
        """Verifica si los datos parecen ser contenido TS válido basado en patrones"""
        if len(data) < 188:  # Tamaño mínimo de paquete TS
            return False
        
        # Verificar si hay patrones repetitivos de 188 bytes (paquetes TS)
        packet_size = 188
        if len(data) >= packet_size * 2:
            # Verificar si hay sync bytes cada 188 bytes
            sync_found = 0
            for i in range(0, min(len(data), packet_size * 5), packet_size):
                if i < len(data) and data[i] == 0x47:
                    sync_found += 1
            
            # Si encontramos al menos 2 sync bytes en posiciones correctas
            if sync_found >= 2:
                return True
        
        # Verificar entropía - datos TS tienen patrones específicos
        unique_bytes = len(set(data[:min(1000, len(data))]))
        entropy_ratio = unique_bytes / min(1000, len(data))
        
        # TS válido tiene entropía media (no muy alta como datos encriptados, no muy baja como datos constantes)
        return 0.3 <= entropy_ratio <= 0.8
    
    def extract_keys_from_m3u8(self, m3u8_content: str) -> List[Dict]:
        """Extrae información de claves de encriptación del contenido M3U8"""
        keys = []
        lines = m3u8_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXT-X-KEY:'):
                key_info = self._parse_key_line(line)
                if key_info:
                    keys.append(key_info)
        
        return keys
    
    def _parse_key_line(self, key_line: str) -> Optional[Dict]:
        """Parsea una línea #EXT-X-KEY"""
        try:
            # Extraer atributos de la línea
            attributes = {}
            parts = key_line.replace('#EXT-X-KEY:', '').split(',')
            
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    # Remover comillas si existen
                    value = value.strip('"')
                    attributes[key.strip()] = value
            
            # Verificar que tenga los campos requeridos
            if 'METHOD' in attributes and 'URI' in attributes:
                return {
                    'method': attributes['METHOD'],
                    'uri': attributes['URI'],
                    'iv': attributes.get('IV', '')
                }
        except Exception as e:
            self.logger.error(f"Error parseando línea de clave: {e}")
        
        return None


def create_aes_decryptor():
    """Factory function para crear un descifrador AES"""
    return AESDecryptor()