#!/usr/bin/env python3
"""
KTP Upload - Zero Dependencies Server
======================================
Minimal server using only Python built-in modules.
No Flask, no pip install needed!

Usage:
  python server.py              # Start on port 8080
  python server.py --port 3000  # Custom port

Requirements: Python 3.6+ (sudah ada di semua Windows)
"""

import http.server
import socketserver
import json
import os
import sys
import socket
import cgi
import io
from pathlib import Path
from datetime import datetime
from urllib.parse import parse_qs

# ─── Config ───
PORT = 8080
OUTPUT_DIR = Path(__file__).parent / "ktp_photos"
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── HTML Page ───
HTML_PAGE = r"""
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
        .header h1 { font-size: 22px; font-weight: 700; }
        .header p { font-size: 13px; color: #94a3b8; margin-top: 4px; }
        
        .card {
            width: 100%;
            max-width: 380px;
            background: #1e293b;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 16px;
        }
        
        .upload-zone {
            border: 2px dashed #475569;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .upload-zone:hover { border-color: #3b82f6; background: rgba(59,130,246,0.1); }
        .upload-zone .icon { font-size: 48px; margin-bottom: 10px; }
        .upload-zone h3 { font-size: 16px; margin-bottom: 4px; }
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
            transition: all 0.2s;
        }
        .btn-primary { background: #3b82f6; color: white; }
        .btn-primary:hover { background: #2563eb; }
        .btn-primary:disabled { background: #475569; cursor: not-allowed; }
        .btn-success { background: #059669; color: white; }
        
        .preview {
            width: 100%;
            margin-top: 12px;
            display: none;
        }
        .preview.show { display: block; }
        .preview img {
            width: 100%;
            border-radius: 10px;
            border: 2px solid #334155;
        }
        .preview .info {
            font-size: 11px;
            color: #64748b;
            text-align: center;
            margin-top: 6px;
        }
        
        .status {
            padding: 12px;
            border-radius: 10px;
            font-size: 13px;
            margin-top: 12px;
            display: none;
        }
        .status.show { display: block; }
        .status.ok { background: #064e3b; color: #6ee7b7; }
        .status.err { background: #7f1d1d; color: #fca5a5; }
        .status.info { background: #1e3a5f; color: #93c5fd; }
        
        .history { margin-top: 20px; width: 100%; max-width: 380px; }
        .history h3 { font-size: 14px; color: #64748b; margin-bottom: 10px; }
        .hist-item {
            background: #1e293b;
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            font-size: 12px;
        }
        .hist-item .name { color: #e2e8f0; }
        .hist-item .time { color: #64748b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📸 KTP Upload</h1>
        <p>Auto-crop & upload ke komputer</p>
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
    
    <div class="history" id="history">
        <h3>📋 Upload Terakhir</h3>
        <div id="histList"></div>
    </div>

<script>
// ─── KTP Auto-Crop (Client-Side) ───
const KTP_RATIO = 85.6 / 53.98;

const zone = document.getElementById('zone');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const preview = document.getElementById('preview');
const previewImg = document.getElementById('previewImg');
const previewInfo = document.getElementById('previewInfo');
const statusEl = document.getElementById('status');
const histList = document.getElementById('histList');

let selectedFile = null;

zone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

function handleFile(file) {
    selectedFile = file;
    uploadBtn.disabled = false;
    const reader = new FileReader();
    reader.onload = e => {
        previewImg.src = e.target.result;
        previewInfo.textContent = file.name + ' (' + (file.size/1024).toFixed(0) + ' KB)';
        preview.classList.add('show');
    };
    reader.readAsDataURL(file);
}

uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Processing...';
    showStatus('info', '⏳ Detecting & cropping KTP...');
    
    try {
        // Step 1: Auto-crop in browser
        const croppedBlob = await autoCropKTP(selectedFile);
        
        if (!croppedBlob) {
            showStatus('err', '❌ KTP tidak terdeteksi. Coba foto dari angle yang lebih frontal.');
            uploadBtn.disabled = false;
            uploadBtn.textContent = '📤 Upload & Crop';
            return;
        }
        
        showStatus('info', '⏳ Uploading...');
        
        // Step 2: Upload cropped image
        const formData = new FormData();
        formData.append('photo', croppedBlob, 'ktp_cropped.jpg');
        
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const result = await resp.json();
        
        if (result.success) {
            showStatus('ok', '✅ Tersimpan: ' + result.filename);
            addHist(result.filename, result.time);
            selectedFile = null;
            fileInput.value = '';
            preview.classList.remove('show');
            setTimeout(() => {
                uploadBtn.disabled = false;
                uploadBtn.textContent = '📤 Upload & Crop';
            }, 1500);
        } else {
            showStatus('err', '❌ ' + result.error);
            uploadBtn.disabled = false;
            uploadBtn.textContent = '📤 Upload & Crop';
        }
    } catch(err) {
        showStatus('err', '❌ Error: ' + err.message);
        uploadBtn.disabled = false;
        uploadBtn.textContent = '📤 Upload & Crop';
    }
});

async function autoCropKTP(file) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Draw image to canvas for pixel access
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            // Convert to grayscale and find edges
            const gray = new Uint8Array(canvas.width * canvas.height);
            for (let i = 0; i < gray.length; i++) {
                const idx = i * 4;
                gray[i] = (data[idx] * 0.299 + data[idx+1] * 0.587 + data[idx+2] * 0.114) | 0;
            }
            
            // Simple edge detection (Sobel-like)
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
            
            // Find bounding box of strong edges
            let minX = canvas.width, maxX = 0, minY = canvas.height, maxY = 0;
            const threshold = 50;
            let edgeCount = 0;
            
            for (let y = 0; y < canvas.height; y++) {
                for (let x = 0; x < canvas.width; x++) {
                    if (edges[y * canvas.width + x] > threshold) {
                        minX = Math.min(minX, x);
                        maxX = Math.max(maxX, x);
                        minY = Math.min(minY, y);
                        maxY = Math.max(maxY, y);
                        edgeCount++;
                    }
                }
            }
            
            // Check if we found enough edges (KTP detected)
            const totalPixels = canvas.width * canvas.height;
            if (edgeCount < totalPixels * 0.01) {
                resolve(null);
                return;
            }
            
            // Add padding
            const pad = 20;
            minX = Math.max(0, minX - pad);
            minY = Math.max(0, minY - pad);
            maxX = Math.min(canvas.width - 1, maxX + pad);
            maxY = Math.min(canvas.height - 1, maxY + pad);
            
            // Calculate crop dimensions
            let cropW = maxX - minX;
            let cropH = maxY - minY;
            
            // Adjust to KTP aspect ratio
            const currentRatio = cropW / cropH;
            if (Math.abs(currentRatio - KTP_RATIO) > 0.3) {
                // Adjust height to match ratio
                cropH = cropW / KTP_RATIO;
            }
            
            // Create cropped canvas
            const outCanvas = document.createElement('canvas');
            const outW = 1200;
            const outH = Math.round(outW / KTP_RATIO);
            outCanvas.width = outW;
            outCanvas.height = outH;
            
            const outCtx = outCanvas.getContext('2d');
            outCtx.drawImage(canvas, minX, minY, cropW, cropH, 0, 0, outW, outH);
            
            // Convert to blob
            outCanvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.92);
        };
        img.src = URL.createObjectURL(file);
    });
}

function showStatus(type, msg) {
    statusEl.className = 'status show ' + type;
    statusEl.textContent = msg;
}

function addHist(name, time) {
    const item = document.createElement('div');
    item.className = 'hist-item';
    item.innerHTML = '<span class="name">' + name + '</span><span class="time">' + time + '</span>';
    histList.insertBefore(item, histList.firstChild);
    while (histList.children.length > 5) histList.removeChild(histList.lastChild);
}

// Load history
fetch('/history').then(r=>r.json()).then(d=>{
    if(d.history) d.history.forEach(h => addHist(h.name, h.time));
});
</script>
</body>
</html>
"""

# ─── Request Handler ───
class KTPHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        
        elif self.path == '/history':
            files = sorted(OUTPUT_DIR.glob("ktp_*.jpg"), reverse=True)[:10]
            history = []
            for f in files:
                ts = f.stem.replace("ktp_", "")
                try:
                    dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
                    t = dt.strftime("%d %b %H:%M")
                except:
                    t = ts
                history.append({"name": f.name, "time": t})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"history": history}).encode())
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                
                if 'multipart/form-data' in content_type:
                    # Parse multipart form data
                    form = cgi.FieldStorage(
                        fp=self.rfile,
                        headers=self.headers,
                        environ={
                            'REQUEST_METHOD': 'POST',
                            'CONTENT_TYPE': content_type,
                        }
                    )
                    
                    file_item = form['photo']
                    
                    if file_item.filename:
                        # Save file
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"ktp_{ts}.jpg"
                        filepath = OUTPUT_DIR / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(file_item.file.read())
                        
                        time_str = datetime.now().strftime("%d %b %H:%M")
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "success": True,
                            "filename": filename,
                            "time": time_str,
                            "path": str(filepath)
                        }).encode())
                    else:
                        self.send_error(400, "No file uploaded")
                else:
                    self.send_error(400, "Invalid content type")
                    
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        # Suppress request logs for cleaner output
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
    parser = argparse.ArgumentParser(description="KTP Upload Server (Zero Dependencies)")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    
    ip = get_local_ip()
    
    print()
    print("=" * 50)
    print("  📸 KTP Upload Server")
    print("  (Zero Dependencies - Python Built-in Only)")
    print("=" * 50)
    print()
    print(f"  📱 Buka di HP:  http://{ip}:{args.port}")
    print(f"  💻 Buka di PC:  http://localhost:{args.port}")
    print()
    print(f"  📁 Foto tersimpan: {OUTPUT_DIR.absolute()}")
    print()
    print("-" * 50)
    print("  ✅ Tidak perlu install apapun!")
    print("  ✅ Auto-crop di browser HP!")
    print("  ✅ Langsung tersimpan di komputer!")
    print("=" * 50)
    print()
    
    with socketserver.TCPServer(("0.0.0.0", args.port), KTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  👋 Server stopped.")


if __name__ == "__main__":
    main()
