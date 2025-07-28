import os
import requests
import subprocess
from urllib.parse import urljoin
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

class M3U8Downloader:
    """
    Versión 4.1: Corregido el error de llamada al método cleanup.
    """
    def __init__(self, m3u8_url: str, output_filename: str = 'output.mp4', max_workers: int = 20, temp_dir: str = 'temp_segments'):
        self.m3u8_url = m3u8_url
        self.output_filename = output_filename
        self.temp_dir = temp_dir
        self.max_workers = max_workers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Accept': '*/*', 
            'Connection': 'keep-alive'
        }

    def _get_segment_urls(self) -> list:
        print("📄 Obteniendo lista de segmentos desde el M3U8...")
        response = requests.get(self.m3u8_url, headers=self.headers)
        response.raise_for_status()
        
        playlist_content = response.text
        lines = playlist_content.splitlines()

        sub_playlists = [line.strip() for line in lines if line.strip().endswith('.m3u8')]
        
        if sub_playlists:
            best_quality_url = urljoin(self.m3u8_url, sub_playlists[-1])
            print(f"ℹ️ Manifiesto maestro detectado. Seleccionando la mejor calidad: {best_quality_url}")
            response = requests.get(best_quality_url, headers=self.headers)
            response.raise_for_status()
            playlist_content = response.text
            lines = playlist_content.splitlines()
            base_url_for_segments = best_quality_url
        else:
            base_url_for_segments = self.m3u8_url

        segment_urls = [urljoin(base_url_for_segments, line.strip()) for line in lines if line and not line.startswith('#') and not line.strip().endswith('.m3u8')]
        
        if not segment_urls:
            if '#EXT-X-KEY' in playlist_content:
                raise ValueError("El video está CIFRADO (#EXT-X-KEY detectado). Este script no puede procesarlo.")
            raise ValueError("No se encontraron segmentos de video (.ts) en el manifiesto.")
            
        print(f"✅ Encontrados {len(segment_urls)} segmentos.")
        return segment_urls

    def _download_segment(self, url: str, index: int) -> str | None:
        segment_filename = f'segment_{index:05d}.ts'
        segment_path = os.path.join(self.temp_dir, segment_filename)
        try:
            response = requests.get(url, headers=self.headers, stream=True, timeout=15)
            response.raise_for_status()
            with open(segment_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.getsize(segment_path) > 0:
                return segment_filename
            else:
                os.remove(segment_path)
                return None
        except requests.exceptions.RequestException:
            return None

    def _download_segments_parallel(self, segment_urls: list) -> list:
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            print(f"📁 Directorio temporal creado en: '{self.temp_dir}'")
        
        successful_segments = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._download_segment, url, i): i for i, url in enumerate(segment_urls)}
            
            for future in tqdm(as_completed(futures), total=len(segment_urls), desc="📥 Descargando segmentos (paralelo)"):
                result = future.result()
                if result:
                    successful_segments.append(result)

        successful_segments.sort()
        return successful_segments
        
    def _merge_segments(self, successful_segments: list):
        if not successful_segments:
            print("\n❌ No se descargó ningún segmento con éxito. No se puede continuar.")
            return

        print(f"\n🧩 Uniendo {len(successful_segments)} segmentos con ffmpeg...")
        
        list_path = os.path.join(self.temp_dir, 'filelist.txt')
        with open(list_path, 'w', encoding='utf-8') as f:
            for segment_filename in successful_segments:
                f.write(f"file '{segment_filename}'\n")

        command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_path, '-c', 'copy', '-y', self.output_filename]
        
        try:
            process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', check=True)
            print(f"✅ ¡Éxito! Video guardado como '{self.output_filename}'")
        except subprocess.CalledProcessError as e:
            print("\n❌ Error durante la unión con ffmpeg:")
            print(e.stderr)
        except FileNotFoundError:
            print("\n❌ Error: 'ffmpeg' no encontrado. Asegúrate de que esté instalado y en el PATH.")

    def _cleanup(self):
        if os.path.exists(self.temp_dir):
            print("🧹 Limpiando archivos temporales...")
            try:
                for filename in os.listdir(self.temp_dir):
                    os.remove(os.path.join(self.temp_dir, filename))
                os.rmdir(self.temp_dir)
                print("🗑️ Directorio temporal eliminado.")
            except OSError as e:
                print(f"Error al limpiar: {e}")

    def download(self):
        try:
            segment_urls = self._get_segment_urls()
            successful_segments = self._download_segments_parallel(segment_urls)
            self._merge_segments(successful_segments)
        except Exception as e:
            print(f"\n🔴 Ha ocurrido un error inesperado: {e}")
        finally:
            # --- LÍNEA CORREGIDA ---
            self._cleanup() # Se llamó a _cleanup con guion bajo

# --- Ejemplo de Uso ---
if __name__ == '__main__':
    M3U8_FILE_URL = "https://v8.lj20250710new.com/20250725/rloz6vaQ/index.m3u8"
    OUTPUT_FILE = "video_descargado.mp4"

    downloader = M3U8Downloader(m3u8_url=M3U8_FILE_URL, output_filename=OUTPUT_FILE, max_workers=20)
    downloader.download()