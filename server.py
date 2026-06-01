#!/usr/bin/env python3
"""
KTP Upload Server
=================
HP uploads photo → Auto-crop → Download di komputer.

Usage:
  python server.py              # Start on port 8080

Requirements: Python 3.6+ (sudah ada di semua Windows)
"""

import http.server
import socketserver
import json
import os
import socket
import cgi
from pathlib import Path
from datetime import datetime

# ─── Config ───
OUTPUT_DIR = Path(__file__).parent / "ktp_photos"
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── HTML untuk HP (Upload Page) ───
HP_PAGE = r"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KTP Upload</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { font-size: 22px; }
        .header p { font-size: 13px; color: #94a3b8; margin-top: 4px; }
        .card {
            width: 100%;
            max-width: 380px;
            background: #1e293b;
            border-radius: 16px;
            padding: 24px;
        }
        .upload-zone {
            border: 2px dashed #475569;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
        }
        .upload-zone:hover { border-color: #3b82f6; }
        .upload-zone .icon { font-size: 48px; }
        .upload-zone h3 { font-size: 16px; margin: 8px 0 4px; }
        .upload-zone p { font-size: 12px; color: #64748b; }
        .upload-zone input { display: none; }
        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
        }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-primary:disabled { background: #475569; }
        .preview { margin-top: 12px; display: none; }
        .preview.show { display: block; }
        .preview img { width: 100%; border-radius: 10px; border: 2px solid #334155; }
        .preview .info { font-size: 11px; color: #64748b; text-align: center; margin-top: 6px; }
        .status { padding: 12px; border-radius: 10px; font-size: 13px; margin-top: 12px; display: none; }
        .status.show { display: block; }
        .status.ok { background: #064e3b; color: #6ee7b7; }
        .status.err { background: #7f1d1d; color: #fca5a5; }
        .status.info { background: #1e3a5f; color: #93c5fd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📸 KTP Upload</h1>
        <p>Foto → Auto-Crop → Download di Komputer</p>
    </div>
    <div class="card">
        <div class="upload-zone" id="zone">
            <div class="icon">📷</div>
            <h3>Ketuk untuk Foto</h3>
            <p>atau pilih dari galeri</p>
            <input type="file" id="fileInput" accept="image/*" capture="environment">
        </div>
        <div class="preview" id="preview">
            <img id="previewImg">
            <div class="info" id="previewInfo"></div>
        </div>
        <button class="btn btn-primary" id="uploadBtn" disabled>📤 Upload & Crop</button>
        <div class="status" id="status"></div>
    </div>
<script>
const KTP_RATIO = 85.6 / 53.98;
const zone = document.getElementById('zone');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const preview = document.getElementById('preview');
const previewImg = document.getElementById('previewImg');
const previewInfo = document.getElementById('previewInfo');
const statusEl = document.getElementById('status');
let selectedFile = null;

zone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

function handleFile(file) {
    selectedFile = file;
    uploadBtn.disabled = false;
    const reader = new FileReader();
    reader.onload = e => {
        previewImg.src = e.target.result;
        previewInfo.textContent = file.name;
        preview.classList.add('show');
    };
    reader.readAsDataURL(file);
}

uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Processing...';
    showStatus('info', '⏳ Cropping KTP...');
    
    try {
        const croppedBlob = await autoCropKTP(selectedFile);
        if (!croppedBlob) {
            showStatus('err', '❌ KTP tidak terdeteksi.');
            uploadBtn.disabled = false;
            uploadBtn.textContent = '📤 Upload & Crop';
            return;
        }
        
        showStatus('info', '⏳ Uploading...');
        const formData = new FormData();
        formData.append('photo', croppedBlob, 'ktp.jpg');
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const result = await resp.json();
        
        if (result.success) {
            showStatus('ok', '✅ Tersimpan! Buka di komputer untuk download.');
            selectedFile = null;
            fileInput.value = '';
            preview.classList.remove('show');
        } else {
            showStatus('err', '❌ ' + result.error);
        }
    } catch(err) {
        showStatus('err', '❌ Error: ' + err.message);
    }
    uploadBtn.disabled = false;
    uploadBtn.textContent = '📤 Upload & Crop';
});

async function autoCropKTP(file) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            const gray = new Uint8Array(canvas.width * canvas.height);
            for (let i = 0; i < gray.length; i++) {
                const idx = i * 4;
                gray[i] = (data[idx] * 0.299 + data[idx+1] * 0.587 + data[idx+2] * 0.114) | 0;
            }
            const edges = new Uint8Array(canvas.width * canvas.height);
            for (let y = 1; y < canvas.height - 1; y++) {
                for (let x = 1; x < canvas.width - 1; x++) {
                    const idx = y * canvas.width + x;
                    const gx = -gray[(y-1)*canvas.width+x-1] + gray[(y-1)*canvas.width+x+1]
                              -2*gray[y*canvas.width+x-1] + 2*gray[y*canvas.width+x+1]
                              -gray[(y+1)*canvas.width+x-1] + gray[(y+1)*canvas.width+x+1];
                    const gy = -gray[(y-1)*canvas.width+x-1] - 2*gray[(y-1)*canvas.width+x] - gray[(y-1)*canvas.width+x+1]
                              +gray[(y+1)*canvas.width+x-1] + 2*gray[(y+1)*canvas.width+x] + gray[(y+1)*canvas.width+x+1];
                    edges[idx] = Math.min(255, Math.sqrt(gx*gx + gy*gy)) | 0;
                }
            }
            let minX = canvas.width, maxX = 0, minY = canvas.height, maxY = 0;
            let edgeCount = 0;
            for (let y = 0; y < canvas.height; y++) {
                for (let x = 0; x < canvas.width; x++) {
                    if (edges[y * canvas.width + x] > 50) {
                        minX = Math.min(minX, x); maxX = Math.max(maxX, x);
                        minY = Math.min(minY, y); maxY = Math.max(maxY, y);
                        edgeCount++;
                    }
                }
            }
            if (edgeCount < (canvas.width * canvas.height * 0.01)) { resolve(null); return; }
            const pad = 20;
            minX = Math.max(0, minX - pad); minY = Math.max(0, minY - pad);
            maxX = Math.min(canvas.width - 1, maxX + pad); maxY = Math.min(canvas.height - 1, maxY + pad);
            let cropW = maxX - minX, cropH = maxY - minY;
            if (Math.abs(cropW / cropH - KTP_RATIO) > 0.3) cropH = cropW / KTP_RATIO;
            const outCanvas = document.createElement('canvas');
            outCanvas.width = 1200; outCanvas.height = Math.round(1200 / KTP_RATIO);
            outCanvas.getContext('2d').drawImage(canvas, minX, minY, cropW, cropH, 0, 0, outCanvas.width, outCanvas.height);
            outCanvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.92);
        };
        img.src = URL.createObjectURL(file);
    });
}

function showStatus(type, msg) {
    statusEl.className = 'status show ' + type;
    statusEl.textContent = msg;
}
</script>
</body>
</html>
"""

# ─── HTML untuk Komputer (Gallery + Download) ───
PC_PAGE_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KTP Photos - Download</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f8fafc;
            color: #1e293b;
            padding: 30px;
        }
        .header { margin-bottom: 30px; }
        .header h1 { font-size: 24px; }
        .header p { font-size: 14px; color: #64748b; margin-top: 4px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: box-shadow 0.2s;
        }
        .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .card img {
            width: 100%;
            height: 180px;
            object-fit: cover;
            cursor: pointer;
        }
        .card .info {
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .card .name { font-size: 13px; font-weight: 500; }
        .card .time { font-size: 11px; color: #94a3b8; }
        .card .btn {
            display: inline-block;
            background: #3b82f6;
            color: white;
            text-decoration: none;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }
        .card .btn:hover { background: #2563eb; }
        .empty {
            text-align: center;
            padding: 60px;
            color: #94a3b8;
        }
        .empty .icon { font-size: 48px; margin-bottom: 12px; }
        .refresh {
            display: inline-block;
            background: #e2e8f0;
            color: #475569;
            padding: 8px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 13px;
            margin-bottom: 20px;
        }
        .refresh:hover { background: #cbd5e1; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📸 KTP Photos</h1>
        <p>Upload dari HP, download di sini</p>
    </div>
    <a class="refresh" href="/pc">🔄 Refresh</a>
    <div class="grid">
        %%ITEMS%%
    </div>
</body>
</html>
"""


class KTPHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/' or self.path == '/hp':
            # Halaman untuk HP
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HP_PAGE.encode('utf-8'))
        
        elif self.path == '/pc':
            # Gallery untuk komputer
            files = sorted(OUTPUT_DIR.glob("ktp_*.jpg"), reverse=True)
            items = ""
            for f in files:
                ts = f.stem.replace("ktp_", "")
                try:
                    dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
                    t = dt.strftime("%d %b %Y, %H:%M")
                except:
                    t = ts
                items += f"""
                <div class="card">
                    <img src="/photo/{f.name}" onclick="window.open('/photo/{f.name}')">
                    <div class="info">
                        <div>
                            <div class="name">{f.name}</div>
                            <div class="time">{t}</div>
                        </div>
                        <a class="btn" href="/download/{f.name}">📥 Download</a>
                    </div>
                </div>
                """
            
            if not items:
                items = '<div class="empty"><div class="icon">📭</div><p>Belum ada foto KTP</p><p style="font-size:12px;margin-top:8px">Upload dari HP dulu!</p></div>'
            
            html = PC_PAGE_TEMPLATE.replace("%%ITEMS%%", items)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path.startswith('/photo/'):
            # Serve photo
            fname = self.path.split('/photo/')[-1]
            fpath = OUTPUT_DIR / fname
            if fpath.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(fpath.read_bytes())
            else:
                self.send_error(404)
        
        elif self.path.startswith('/download/'):
            # Download photo
            fname = self.path.split('/download/')[-1]
            fpath = OUTPUT_DIR / fname
            if fpath.exists():
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
                self.end_headers()
                self.wfile.write(fpath.read_bytes())
            else:
                self.send_error(404)
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in content_type:
                    form = cgi.FieldStorage(
                        fp=self.rfile,
                        headers=self.headers,
                        environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type}
                    )
                    file_item = form['photo']
                    if file_item.filename:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"ktp_{ts}.jpg"
                        filepath = OUTPUT_DIR / filename
                        with open(filepath, 'wb') as f:
                            f.write(file_item.file.read())
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True, "filename": filename}).encode())
                    else:
                        self.send_error(400, "No file")
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KTP Upload Server")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    
    ip = get_local_ip()
    
    print()
    print("=" * 50)
    print("  📸 KTP Upload Server")
    print("=" * 50)
    print()
    print(f"  📱 HP:    http://{ip}:{args.port}/hp")
    print(f"  💻 PC:    http://localhost:{args.port}/pc")
    print()
    print(f"  📁 Folder: {OUTPUT_DIR.absolute()}")
    print()
    print("-" * 50)
    print("  1. Buka /hp di HP → Foto KTP")
    print("  2. Buka /pc di komputer → Download")
    print("=" * 50)
    print()
    
    with socketserver.TCPServer(("0.0.0.0", args.port), KTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  👋 Stopped.")


if __name__ == "__main__":
    main()
