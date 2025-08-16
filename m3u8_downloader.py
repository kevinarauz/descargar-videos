import os
import time
from typing import Optional, Callable, List, Tuple, Union
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import solo de las funciones específicas necesarias
from subprocess import CompletedProcess, CalledProcessError, run
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import subprocess

class M3U8Downloader:
    """
    Versión 4.2: Soporte completo para streams dinámicos y live streams.
    - Detecta automáticamente si es VOD o LIVE stream
    - Sigue actualizaciones de playlist hasta encontrar #EXT-X-ENDLIST
    - Recopila todos los segmentos disponibles, no solo los iniciales
    - Evita duplicados usando sets
    - Timeout inteligente para streams que no se actualizan
    """
    def __init__(self, m3u8_url: str, output_filename: str = 'output.mp4', max_workers: int = 30, temp_dir: str = 'temp_segments', download_id: Optional[str] = None, log_function: Optional[Callable[[str], None]] = None):
        self.m3u8_url = m3u8_url
        self.output_filename = output_filename
        self.temp_dir = temp_dir
        self.download_id = download_id
        self.log_function = log_function or print
        # Aumentar workers para mayor paralelismo
        self.max_workers = max_workers
        # Headers optimizados para mejor rendimiento
        parsed = urlparse(self.m3u8_url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': '*/*', 
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',  # Compresión para reducir transferencia
            'Cache-Control': 'no-cache',
            **({'Referer': origin + '/','Origin': origin} if origin else {})
        }
        # Session reutilizable para conexiones persistentes
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Configuración optimizada de la sesión
        adapter = HTTPAdapter(
            pool_connections=max_workers,  # Pool de conexiones
            pool_maxsize=max_workers * 2,  # Tamaño máximo del pool
            max_retries=3,  # Reintentos automáticos
            pool_block=False  # No bloquear cuando el pool está lleno
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def _get_segment_urls(self) -> List[str]:
        self.log_function("📄 Obteniendo lista de segmentos desde el M3U8...")
        response = self.session.get(self.m3u8_url, timeout=10)
        response.raise_for_status()
        
        playlist_content = response.text
        lines = playlist_content.splitlines()

        sub_playlists = [line.strip() for line in lines if line.strip().endswith('.m3u8')]
        
        if sub_playlists:
            best_quality_url = urljoin(self.m3u8_url, sub_playlists[-1])
            self.log_function(f"ℹ️ Manifiesto maestro detectado. Seleccionando la mejor calidad: {best_quality_url}")
            response = self.session.get(best_quality_url, timeout=10)
            response.raise_for_status()
            playlist_content = response.text
            lines = playlist_content.splitlines()
            base_url_for_segments = best_quality_url
        else:
            base_url_for_segments = self.m3u8_url

        # Verificar si es un stream en vivo o VOD completo
        is_live_stream = '#EXT-X-PLAYLIST-TYPE:VOD' not in playlist_content
        has_endlist = '#EXT-X-ENDLIST' in playlist_content
        
        self.log_function(f"🔍 Tipo de stream: {'LIVE/Dinámico' if is_live_stream else 'VOD'}")
        self.log_function(f"🔍 Marcador de fin: {'Encontrado' if has_endlist else 'No encontrado'}")
        
        # Recopilar todos los segmentos disponibles
        segment_urls = self._collect_all_segments(base_url_for_segments, playlist_content, is_live_stream, has_endlist)
        
        if not segment_urls:
            if '#EXT-X-KEY' in playlist_content:
                raise ValueError("El video está CIFRADO (#EXT-X-KEY detectado). Este script no puede procesarlo.")
            raise ValueError("No se encontraron segmentos de video (.ts) en el manifiesto.")
            
        self.log_function(f"✅ Encontrados {len(segment_urls)} segmentos totales.")
        if len(segment_urls) == 0:
            self.log_function("⚠️ ADVERTENCIA: No se encontraron segmentos en la playlist!")
            self.log_function(f"🔍 Contenido de playlist recibido:")
            self.log_function(playlist_content[:500] + "..." if len(playlist_content) > 500 else playlist_content)
        return segment_urls

    def _collect_all_segments(self, base_url: str, initial_content: str, is_live: bool, has_endlist: bool) -> List[str]:
        """Recopila todos los segmentos disponibles, siguiendo actualizaciones si es necesario"""
        all_segments = set()  # Usar set para evitar duplicados
        current_content = initial_content
        
        # Extraer segmentos del contenido inicial
        lines = current_content.splitlines()
        initial_segments = [urljoin(base_url, line.strip()) for line in lines 
                          if line and not line.startswith('#') and not line.strip().endswith('.m3u8')]
        all_segments.update(initial_segments)
        self.log_function(f"📊 Segmentos iniciales encontrados: {len(initial_segments)}")
        
        # Si es VOD con ENDLIST, ya tenemos todos los segmentos
        if not is_live and has_endlist:
            return list(all_segments)
        
        # Si es live stream o no tiene ENDLIST, seguir buscando actualizaciones
        if is_live or not has_endlist:
            self.log_function("🔄 Stream dinámico detectado. Buscando segmentos adicionales...")
            max_attempts = 10  # Máximo 10 intentos para evitar bucles infinitos
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # Esperar un poco antes de la siguiente consulta
                    if attempt > 0:
                        self.log_function(f"⏳ Esperando nuevos segmentos... (intento {attempt + 1}/{max_attempts})")
                        time.sleep(3)
                    
                    # Obtener playlist actualizada
                    response = self.session.get(base_url, timeout=10)
                    response.raise_for_status()
                    updated_content = response.text
                    
                    # Extraer nuevos segmentos
                    lines = updated_content.splitlines()
                    new_segments = [urljoin(base_url, line.strip()) for line in lines 
                                  if line and not line.startswith('#') and not line.strip().endswith('.m3u8')]
                    
                    previous_count = len(all_segments)
                    all_segments.update(new_segments)
                    new_count = len(all_segments)
                    
                    if new_count > previous_count:
                        self.log_function(f"🆕 Encontrados {new_count - previous_count} segmentos adicionales (total: {new_count})")
                    
                    # Verificar si ahora tiene ENDLIST
                    if '#EXT-X-ENDLIST' in updated_content:
                        self.log_function("🏁 Marcador de fin encontrado. Stream completo.")
                        break
                    
                    # Si no hay nuevos segmentos en varias iteraciones, probablemente terminó
                    if new_count == previous_count:
                        attempt += 1
                    else:
                        attempt = 0  # Reiniciar contador si encontramos nuevos segmentos
                        
                except Exception as e:
                    self.log_function(f"⚠️ Error al buscar actualizaciones: {e}")
                    break
        
        return list(all_segments)

    def _validate_ts_segment(self, segment_path: str) -> bool:
        """Valida que un archivo sea un segmento MPEG-TS válido"""
        try:
            if not os.path.exists(segment_path):
                return False
                
            file_size = os.path.getsize(segment_path)
            if file_size < 188:  # Tamaño mínimo de un paquete MPEG-TS
                return False
            
            # MPEG-TS debe comenzar con sync byte 0x47
            with open(segment_path, 'rb') as f:
                first_bytes = f.read(16)  # Leer más bytes para mejor detección
                
                # Buscar sync byte 0x47 al inicio o en las primeras posiciones
                # A veces hay headers antes del sync byte
                for i in range(min(4, len(first_bytes))):
                    if first_bytes[i] == 0x47:
                        return True
                
                # Si no encontramos 0x47, verificar si es un archivo de error HTML/texto
                try:
                    text_content = first_bytes.decode('utf-8', errors='ignore').lower()
                    if any(keyword in text_content for keyword in ['<html', '<!doctype', 'error', '404', '403']):
                        return False
                except:
                    pass
                    
                return False
        except Exception as e:
            return False

    def _download_segment(self, url: str, index: int) -> Optional[Tuple[str, int]]:
        segment_filename = f'segment_{index:05d}.ts'
        segment_path = os.path.join(self.temp_dir, segment_filename)
        try:
            # Log detallado para debugging
            self.log_function(f"🔍 Descargando segmento {index}: {url}")
            
            response = self.session.get(url, headers=self.headers, stream=True, timeout=15)
            response.raise_for_status()
            
            # Log de la respuesta
            self.log_function(f"📥 Segmento {index} - Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}, Size: {response.headers.get('content-length', 'N/A')}")
            
            # Verificar Content-Type si está disponible
            content_type = response.headers.get('content-type', '').lower()
            if content_type and 'text/html' in content_type:
                self.log_function(f"⚠️ Segmento {index} devolvió HTML en lugar de video (posible error 404/403)")
                return None
            
            bytes_downloaded = 0
            with open(segment_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
            
            file_size = os.path.getsize(segment_path)
            if file_size > 0:
                # Validar que el segmento sea un archivo MPEG-TS válido
                if self._validate_ts_segment(segment_path):
                    self.log_function(f"✅ Segmento {index} validado correctamente")
                    return (segment_filename, bytes_downloaded)
                else:
                    # Log detallado del archivo rechazado
                    self.log_function(f"⚠️ Segmento {index} descargado pero no es MPEG-TS válido")
                    self.log_function(f"📁 Archivo: {segment_path}, Tamaño: {os.path.getsize(segment_path)} bytes")
                    
                    # Mostrar primeros bytes para debugging y detectar tipo de corrupción
                    try:
                        with open(segment_path, 'rb') as f:
                            first_bytes = f.read(16)
                            self.log_function(f"🔍 Primeros bytes: {first_bytes.hex()}")
                            
                            # Detectar tipos comunes de corrupción
                            if first_bytes[:4] == b'\x83\xe1\x38\x99':
                                self.log_function(f"🔐 DETECIDO: Contenido encriptado/comprimido - el servidor devuelve datos protegidos")
                            elif first_bytes.startswith(b'<html') or first_bytes.startswith(b'<!DOCTYPE'):
                                self.log_function(f"🌐 DETECTADO: Página HTML - posible error 404/403 del servidor")
                            elif all(b == 0 for b in first_bytes):
                                self.log_function(f"🚫 DETECTADO: Archivo vacío/nulo")
                            else:
                                self.log_function(f"❓ DETECTADO: Formato desconocido - posible corrupción de red")
                    except:
                        pass
                    
                    self.log_function(f"🗑️ Eliminando segmento {index}")
                    os.remove(segment_path)
                    return None
            else:
                if os.path.exists(segment_path):
                    os.remove(segment_path)
                return None
        except requests.exceptions.RequestException as e:
            self.log_function(f"⚠️ Error descargando segmento {index}: {e}")
            return None

    def _download_segments_parallel(self, segment_urls: List[str]) -> List[str]:
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            self.log_function(f"📁 Directorio temporal creado en: '{self.temp_dir}'")
        
        successful_segments = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_segment, url, i): i for i, url in enumerate(segment_urls)}
            
            for future in tqdm(as_completed(futures), total=len(segment_urls), desc="📥 Descargando segmentos (paralelo)"):
                result = future.result()
                if result:
                    segment_filename, bytes_downloaded = result
                    successful_segments.append(segment_filename)

        successful_segments.sort()
        self.log_function(f"📥 Descarga de segmentos completada: {len(successful_segments)}/{len(segment_urls)} exitosos")
        return successful_segments
        
    def _merge_segments(self, successful_segments: List[str]) -> None:
        if not successful_segments:
            self.log_function("\n❌ No se descargó ningún segmento con éxito. No se puede continuar.")
            return

        self.log_function(f"\n🧩 Uniendo {len(successful_segments)} segmentos con ffmpeg...")
        
        list_path = os.path.join(self.temp_dir, 'filelist.txt')
        
        # Verificar que los segmentos existen y son válidos antes de crear la lista
        valid_segments = []
        invalid_count = 0
        for segment_filename in successful_segments:
            segment_path = os.path.join(self.temp_dir, segment_filename)
            if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0:
                # Validar que es un archivo MPEG-TS válido
                if self._validate_ts_segment(segment_path):
                    valid_segments.append(segment_path)
                else:
                    invalid_count += 1
                    self.log_function(f"⚠️ Segmento corrupto encontrado: {segment_filename}")
            else:
                self.log_function(f"⚠️ Segmento faltante o vacío: {segment_filename}")
        
        if invalid_count > 0:
            self.log_function(f"🔍 Se encontraron {invalid_count} segmentos corruptos de {len(successful_segments)} total")
        
        if not valid_segments:
            self.log_function("❌ No hay segmentos válidos para unir! Todos los segmentos están corruptos o vacíos.")
            return
            
        if len(valid_segments) < len(successful_segments) * 0.8:  # Si perdemos más del 20% de segmentos
            self.log_function(f"⚠️ ADVERTENCIA: Solo {len(valid_segments)}/{len(successful_segments)} segmentos son válidos. El video final puede estar incompleto.")
            
        self.log_function(f"📋 Creando lista de {len(valid_segments)} segmentos válidos...")
        
        # Escribir lista de archivos con rutas absolutas y escape correcto
        with open(list_path, 'w', encoding='utf-8') as f:
            for segment_path in valid_segments:
                # Usar rutas absolutas y escapar comillas para FFmpeg
                abs_path = os.path.abspath(segment_path).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        # Asegurar que el directorio de salida existe
        output_dir = os.path.dirname(os.path.abspath(self.output_filename))
        os.makedirs(output_dir, exist_ok=True)
        
        # Comando FFmpeg mejorado con más opciones de compatibilidad
        command = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_path,
            '-c', 'copy', '-avoid_negative_ts', 'make_zero',
            '-fflags', '+genpts', '-y', self.output_filename
        ]
        
        self.log_function(f"🔧 Comando FFmpeg: {' '.join(command)}")
        
        try:
            # Ejecutar ffmpeg para unir los segmentos
            process: CompletedProcess[str] = run(
                command, capture_output=True, text=True, encoding='utf-8', check=True
            )
            
            self.log_function(f"📤 FFmpeg stdout: {process.stdout}")
            
            # Verificar que el archivo de salida existe y no está vacío
            if os.path.exists(self.output_filename):
                file_size = os.path.getsize(self.output_filename)
                self.log_function(f"✅ ¡Éxito! Video guardado como '{self.output_filename}' (tamaño: {file_size:,} bytes)")
                if file_size == 0:
                    self.log_function("⚠️ ADVERTENCIA: El archivo de salida está vacío!")
            else:
                self.log_function(f"⚠️ ADVERTENCIA: El archivo de salida '{self.output_filename}' no fue creado!")
                
        except CalledProcessError as e:
            self.log_function("\n❌ Error durante la unión con ffmpeg:")
            self.log_function(f"📤 FFmpeg stdout: {e.stdout}")
            self.log_function(f"📤 FFmpeg stderr: {e.stderr}")
            self.log_function(f"📤 Código de salida: {e.returncode}")
            
            # Información adicional para debugging
            self.log_function(f"📋 Lista de archivos usada: {list_path}")
            if os.path.exists(list_path):
                with open(list_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_function(f"📄 Contenido de filelist.txt:\n{content}")
                    
        except FileNotFoundError:
            self.log_function("\n❌ Error: 'ffmpeg' no encontrado. Asegúrate de que esté instalado y en el PATH.")
            self.log_function("💡 Descarga FFmpeg desde: https://ffmpeg.org/download.html")

    def _cleanup(self) -> None:
        if os.path.exists(self.temp_dir):
            self.log_function("🧹 Limpiando archivos temporales...")
            try:
                for filename in os.listdir(self.temp_dir):
                    os.remove(os.path.join(self.temp_dir, filename))
                os.rmdir(self.temp_dir)
                self.log_function("🗑️ Directorio temporal eliminado.")
            except OSError as e:
                self.log_function(f"Error al limpiar: {e}")

    def download(self) -> None:
        try:
            segment_urls = self._get_segment_urls()
            successful_segments = self._download_segments_parallel(segment_urls)
            self._merge_segments(successful_segments)
        except Exception as e:
            self.log_function(f"\n🔴 Ha ocurrido un error inesperado: {e}")
        finally:
            # --- LÍNEA CORREGIDA ---
            self._cleanup() # Se llamó a _cleanup con guion bajo

# --- Ejemplo de Uso ---
if __name__ == '__main__':
    M3U8_FILE_URL = "https://example.com/path/to/your/video.m3u8"
    OUTPUT_FILE = "video_descargado.mp4"

    downloader = M3U8Downloader(m3u8_url=M3U8_FILE_URL, output_filename=OUTPUT_FILE, max_workers=20)
    downloader.download()