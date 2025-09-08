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
                
                # Determinar clave de descifrado apropiada
                decryption_key = self._select_decryption_key(decryption_keys, i)
                if not decryption_key:
                    results['failed_segments'] += 1
                    results['errors'].append(f"No hay clave disponible para segmento {i}")
                    continue
                
                # Descifrar segmento
                decrypted_data = self._decrypt_segment_aes128(encrypted_data, decryption_key, i)
                if not decrypted_data:
                    results['failed_segments'] += 1
                    results['errors'].append(f"Fallo al descifrar segmento {i}")
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
        """Selecciona la clave apropiada para un segmento"""
        if not keys:
            return None
        
        # Por ahora usar la primera clave disponible
        # En implementaciones más avanzadas se podría determinar por patrones en las URLs
        return list(keys.values())[0]
    
    def _decrypt_segment_aes128(self, encrypted_data: bytes, key: bytes, segment_index: int) -> Optional[bytes]:
        """Descifra un segmento usando AES-128"""
        try:
            # Vector de inicialización (IV) para HLS es típicamente el índice del segmento
            iv = struct.pack('>Q', segment_index) + b'\x00' * 8  # IV de 16 bytes
            
            # Crear cipher AES-128-CBC
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # Descifrar datos
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Remover padding PKCS7
            try:
                decrypted_data = unpad(decrypted_data, AES.block_size)
            except ValueError:
                # Si falla el unpad, es posible que no haya padding
                pass
            
            # Verificar que el resultado sea un segmento TS válido
            if len(decrypted_data) > 0 and decrypted_data[0] == 0x47:
                return decrypted_data
            else:
                # Intentar con IV=0 (algunos streams usan IV constante)
                iv_zero = b'\x00' * 16
                cipher_zero = AES.new(key, AES.MODE_CBC, iv_zero)
                decrypted_data = cipher_zero.decrypt(encrypted_data)
                
                try:
                    decrypted_data = unpad(decrypted_data, AES.block_size)
                except ValueError:
                    pass
                
                if len(decrypted_data) > 0 and decrypted_data[0] == 0x47:
                    return decrypted_data
                else:
                    self.logger.warning(f"Segmento descifrado {segment_index} no tiene sync byte válido")
                    return decrypted_data  # Devolver aunque no sea válido para debug
                    
        except Exception as e:
            self.logger.error(f"Error descifrando segmento {segment_index}: {e}")
            return None
    
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