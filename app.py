import threading
from flask import jsonify, session
# Variable global para el progreso
download_progress = {
    'total': 0,
    'current': 0,
    'status': 'idle',
    'error': '',
    'porcentaje': 0
}
from flask import Flask, render_template_string, request, send_file, session, url_for
import os
from test import M3U8Downloader
import glob

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia esto por una clave segura en producción

# Diccionario para progreso de descargas múltiples
multi_progress = {}

default_html = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Descargador M3U8 Mejorado</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: #fff; }
        .sidebar { background: #222; min-height: 100vh; padding: 2rem 1rem; }
        .sidebar h3 { color: #fff; }
        .sidebar ul { list-style: none; padding: 0; }
        .sidebar li { margin-bottom: 0.7rem; }
        .sidebar a { color: #90caf9; text-decoration: none; }
        .sidebar a:hover { text-decoration: underline; }
        .main { padding: 2rem; }
        .credit { margin-top: 2rem; font-size: 0.9rem; color: #ccc; text-align: center; }
    </style>
</head>
<body>
<div class="container-fluid">
  <div class="row">
    <nav class="col-md-3 sidebar">
      <h3>Historial de descargas</h3>
      {% if historial and historial|length > 0 %}
        <ul>
        {% for item in historial %}
          <li><a href="/static/{{item.archivo}}" download>{{item.archivo}}</a></li>
        {% endfor %}
        </ul>
      {% else %}
        <span style="color:#ccc">No hay descargas aún.</span>
      {% endif %}
      <hr>
      <h3>Descargas activas</h3>
      <div id="descargas-activas"></div>
    </nav>
    <main class="col-md-9 main">
      <h1>Descargar y reproducir M3U8</h1>
      <form id="descargar-form" class="mb-4">
        <input type="text" name="m3u8_url" id="m3u8-url" class="form-control mb-2" placeholder="Pega aquí la URL M3U8..." value="{{ url }}">
        <input type="text" name="output_name" id="output-name" class="form-control mb-2" placeholder="Nombre del archivo MP4 (opcional)">
        <button type="button" class="btn btn-info me-2" onclick="playM3U8()">Reproducir</button>
        <button type="submit" class="btn btn-success">Descargar MP4</button>
      </form>
      <div id="video-container"></div>
      <div id="progreso" class="mt-4"></div>
      <div class="credit">Desarrollado con <a href="https://github.com/video-dev/hls.js/" target="_blank" style="color:#fff;text-decoration:underline;">hls.js</a> + Flask + Python + Bootstrap</div>
    </main>
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
function playM3U8() {
    const url = document.getElementById('m3u8-url').value.trim();
    const container = document.getElementById('video-container');
    container.innerHTML = '';
    if (!url) {
        container.innerHTML = '<p>Por favor ingresa una URL M3U8 válida.</p>';
        return;
    }
    const video = document.createElement('video');
    video.controls = true;
    video.autoplay = true;
    video.style.marginTop = '1rem';
    container.appendChild(video);
    if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(url);
        hls.attachMedia(video);
        hls.on(Hls.Events.ERROR, function(event, data) {
            if (data.fatal) {
                container.innerHTML = '<p style="color:#ff8080">Error al cargar el video M3U8.</p>';
            }
        });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = url;
        video.addEventListener('error', function() {
            container.innerHTML = '<p style="color:#ff8080">Error al cargar el video M3U8.</p>';
        });
    } else {
        container.innerHTML = '<p>Tu navegador no soporta reproducción M3U8.</p>';
    }
}
document.getElementById('descargar-form').addEventListener('submit', function(e) {
    e.preventDefault();
    let url = document.getElementById('m3u8-url').value.trim();
    let outputName = document.getElementById('output-name').value.trim();
    let params = 'm3u8_url=' + encodeURIComponent(url);
    if (outputName) params += '&output_name=' + encodeURIComponent(outputName);
    fetch('/descargar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params
    }).then(r => r.json()).then(data => {
        if (data.download_id) {
            mostrarDescargaActiva(data.download_id);
        }
    });
});
function mostrarDescargaActiva(download_id) {
    let div = document.getElementById('descargas-activas');
    let barra = document.createElement('div');
    barra.id = 'descarga-' + download_id;
    barra.innerHTML = `<div><strong id='archivo-${download_id}'>Preparando descarga...</strong></div><div>Progreso: <span id='progreso-${download_id}'>0%</span></div><div class='progress'><div class='progress-bar' id='bar-${download_id}' role='progressbar' style='width:0%'></div></div>`;
    div.appendChild(barra);
    actualizarProgreso(download_id);
}
function actualizarProgreso(download_id) {
    fetch('/progreso/' + download_id).then(r => r.json()).then(data => {
        let bar = document.getElementById('bar-' + download_id);
        let prog = document.getElementById('progreso-' + download_id);
        let archivo = document.getElementById('archivo-' + download_id);
        if (data.output_file && archivo) {
            archivo.innerText = `📥 ${data.output_file}`;
        }
        if (data.status === 'downloading') {
            bar.style.width = data.porcentaje + '%';
            prog.innerText = data.porcentaje + '%';
            setTimeout(function() { actualizarProgreso(download_id); }, 1000);
        } else if (data.status === 'done') {
            bar.style.width = '100%';
            prog.innerText = '100%';
            if (archivo) archivo.innerText = `✅ ${data.output_file}`;
            document.getElementById('descarga-' + download_id).innerHTML += `<div class='mt-2'><a href='/static/${data.output_file}' download class='btn btn-primary btn-sm'>Descargar MP4</a></div>`;
        } else if (data.status === 'error') {
            if (archivo) archivo.innerText = `❌ ${data.output_file || 'Error'}`;
            document.getElementById('descarga-' + download_id).innerHTML += `<div class='mt-2 text-danger'>${data.error}</div>`;
        }
    });
}
</script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    url = request.args.get('url', '')
    # Historial: todos los archivos MP4 en static
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    archivos = []
    if os.path.exists(static_dir):
        for f in glob.glob(os.path.join(static_dir, '*.mp4')):
            archivos.append({'archivo': os.path.basename(f)})
    return render_template_string(default_html, url=url, historial=archivos)

@app.route('/descargar', methods=['POST'])
def descargar():
    m3u8_url = request.form.get('m3u8_url')
    output_name = request.form.get('output_name', '').strip()
    if output_name:
        import re
        output_name = re.sub(r'[^\w\-. ]', '', output_name)
        if not output_name.lower().endswith('.mp4'):
            output_name += '.mp4'
        output_file = output_name
    else:
        output_file = 'video_descargado.mp4'
    if not m3u8_url:
        return 'URL M3U8 no proporcionada', 400
    # ID único para la descarga
    import uuid
    download_id = str(uuid.uuid4())
    multi_progress[download_id] = {
        'total': 0,
        'current': 0,
        'status': 'downloading',
        'error': '',
        'porcentaje': 0,
        'output_file': output_file
    }
    def run_download():
        try:
            # Usar el directorio temp_segments común (como en el clásico)
            temp_dir = os.path.join(os.path.dirname(__file__), 'temp_segments')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            original_dir = os.getcwd()
            # Descarga de segmentos en temp_dir común
            downloader = M3U8Downloader(m3u8_url=m3u8_url, output_filename=output_file, max_workers=20)
            segment_urls = downloader._get_segment_urls()
            multi_progress[download_id]['total'] = len(segment_urls)
            for i, url in enumerate(segment_urls):
                try:
                    downloader._download_segment(url, i)
                    seg_path = os.path.join(temp_dir, f'segment_{i:05d}.ts')
                    if not os.path.exists(seg_path):
                        raise FileNotFoundError(f"No se encontró el archivo {seg_path} tras la descarga.")
                except Exception as err:
                    multi_progress[download_id]['error'] = f"Error al descargar el segmento {i+1}: {err}"
                    multi_progress[download_id]['status'] = 'error'
                    break
                porcentaje = int(((i + 1) / len(segment_urls)) * 100) if len(segment_urls) > 0 else 0
                multi_progress[download_id]['current'] = i + 1
                multi_progress[download_id]['porcentaje'] = porcentaje
            # Fusión y movimiento del archivo MP4
            if multi_progress[download_id]['status'] == 'downloading':
                segment_files = [f'segment_{i:05d}.ts' for i in range(len(segment_urls))]
                print(f"[DEBUG] Segment files: {segment_files}")
                downloader._merge_segments(segment_files)
                static_dir = os.path.join(os.path.dirname(__file__), 'static')
                if not os.path.exists(static_dir):
                    os.makedirs(static_dir)
                static_path = os.path.join(static_dir, output_file)
                output_path = os.path.abspath(os.path.join(original_dir, output_file))
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    os.replace(output_path, static_path)
                    multi_progress[download_id]['status'] = 'done'
                else:
                    multi_progress[download_id]['status'] = 'error'
                    multi_progress[download_id]['error'] = 'No se pudo descargar el video o el archivo está vacío.'
            # No eliminar temp_segments para permitir descargas simultáneas
        except Exception as e:
            multi_progress[download_id]['status'] = 'error'
            multi_progress[download_id]['error'] = str(e)
    thread = threading.Thread(target=run_download)
    thread.start()
    return jsonify({'download_id': download_id}), 202

@app.route('/progreso/<download_id>', methods=['GET'])
def progreso(download_id):
    if download_id not in multi_progress:
        return jsonify({'status': 'error', 'error': 'ID de descarga no encontrado.'}), 404
    return jsonify(multi_progress[download_id]), 200

@app.route('/static/<path:filename>', methods=['GET'])
def serve_static(filename):
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_file(os.path.join(static_dir, filename))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
