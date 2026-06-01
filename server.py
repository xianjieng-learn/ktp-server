#!/usr/bin/env python3
"""
KTP Upload Server
=================
Simple web server for uploading KTP photos from phone.
Photos are auto-cropped and saved to local folder.

Usage:
  python server.py                    # Start on port 8080
  python server.py --port 3000        # Custom port
  python server.py --open             # Auto-open browser

Then on your phone:
  1. Make sure phone & computer are on same WiFi
  2. Open browser → http://<computer-ip>:8080
  3. Take photo or upload from gallery
  4. KTP is auto-cropped and saved!
"""

import cv2
import numpy as np
import os
import sys
import time
import socket
import argparse
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string

# ─── Config ───
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "ktp_photos"
KTP_ASPECT_RATIO = 85.6 / 53.98
OUTPUT_WIDTH = 1200
OUTPUT_HEIGHT = int(OUTPUT_WIDTH / KTP_ASPECT_RATIO)

app = Flask(__name__)

# ─── HTML Template ───
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>KTP Upload</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .header p {
            font-size: 14px;
            color: #94a3b8;
        }
        .upload-area {
            width: 100%;
            max-width: 400px;
            background: #1e293b;
            border: 3px dashed #475569;
            border-radius: 20px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: #3b82f6;
            background: #1e3a5f;
        }
        .upload-area .icon {
            font-size: 64px;
            margin-bottom: 15px;
        }
        .upload-area h2 {
            font-size: 18px;
            margin-bottom: 8px;
        }
        .upload-area p {
            font-size: 13px;
            color: #94a3b8;
        }
        .upload-area input[type="file"] {
            display: none;
        }
        .btn {
            display: inline-block;
            background: #3b82f6;
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
            width: 100%;
            max-width: 400px;
            transition: background 0.2s;
        }
        .btn:hover { background: #2563eb; }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { background: #475569; cursor: not-allowed; }
        
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 12px;
            width: 100%;
            max-width: 400px;
            display: none;
        }
        .status.show { display: block; }
        .status.success { background: #065f46; color: #6ee7b7; }
        .status.error { background: #7f1d1d; color: #fca5a5; }
        .status.processing { background: #1e3a5f; color: #93c5fd; }
        
        .preview {
            margin-top: 20px;
            width: 100%;
            max-width: 400px;
            display: none;
        }
        .preview.show { display: block; }
        .preview img {
            width: 100%;
            border-radius: 12px;
            border: 2px solid #334155;
        }
        .preview .label {
            font-size: 12px;
            color: #94a3b8;
            margin-top: 8px;
            text-align: center;
        }
        
        .history {
            margin-top: 30px;
            width: 100%;
            max-width: 400px;
        }
        .history h3 {
            font-size: 16px;
            margin-bottom: 10px;
            color: #94a3b8;
        }
        .history-item {
            background: #1e293b;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .history-item .name {
            font-size: 13px;
            color: #e2e8f0;
        }
        .history-item .time {
            font-size: 11px;
            color: #64748b;
        }
        .history-item .badge {
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 6px;
            background: #065f46;
            color: #6ee7b7;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📸 KTP Upload</h1>
        <p>Foto KTP → Auto-Crop → Tersimpan</p>
    </div>
    
    <div class="upload-area" id="dropZone">
        <div class="icon">📷</div>
        <h2>Ketuk untuk Foto/Upload</h2>
        <p>atau drag & drop file di sini</p>
        <input type="file" id="fileInput" accept="image/*" capture="environment">
    </div>
    
    <button class="btn" id="uploadBtn" disabled>📤 Upload & Crop</button>
    
    <div class="status" id="status"></div>
    
    <div class="preview" id="preview">
        <img id="previewImg" src="" alt="Preview">
        <div class="label" id="previewLabel"></div>
    </div>
    
    <div class="history" id="history">
        <h3>📋 Upload Terakhir</h3>
        <div id="historyList"></div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const status = document.getElementById('status');
        const preview = document.getElementById('preview');
        const previewImg = document.getElementById('previewImg');
        const previewLabel = document.getElementById('previewLabel');
        const historyList = document.getElementById('historyList');
        
        let selectedFile = null;
        
        // Click to upload
        dropZone.addEventListener('click', () => fileInput.click());
        
        // File selected
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        // Drag & drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });
        
        function handleFile(file) {
            selectedFile = file;
            uploadBtn.disabled = false;
            
            // Show preview
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                previewLabel.textContent = file.name;
                preview.classList.add('show');
            };
            reader.readAsDataURL(file);
        }
        
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            uploadBtn.disabled = true;
            uploadBtn.textContent = '⏳ Uploading...';
            showStatus('processing', '⏳ Mengupload & memproses KTP...');
            
            const formData = new FormData();
            formData.append('photo', selectedFile);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showStatus('success', `✅ Berhasil! Tersimpan: ${result.filename}`);
                    addHistory(result.filename, result.timestamp);
                    
                    // Reset
                    selectedFile = null;
                    fileInput.value = '';
                    preview.classList.remove('show');
                    setTimeout(() => {
                        uploadBtn.disabled = false;
                        uploadBtn.textContent = '📤 Upload & Crop';
                    }, 2000);
                } else {
                    showStatus('error', `❌ ${result.error}`);
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = '📤 Upload & Crop';
                }
            } catch (err) {
                showStatus('error', `❌ Error: ${err.message}`);
                uploadBtn.disabled = false;
                uploadBtn.textContent = '📤 Upload & Crop';
            }
        });
        
        function showStatus(type, msg) {
            status.className = `status show ${type}`;
            status.textContent = msg;
        }
        
        function addHistory(filename, timestamp) {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.innerHTML = `
                <div>
                    <div class="name">${filename}</div>
                    <div class="time">${timestamp}</div>
                </div>
                <div class="badge">✅ Cropped</div>
            `;
            historyList.insertBefore(item, historyList.firstChild);
            
            // Keep only last 5
            while (historyList.children.length > 5) {
                historyList.removeChild(historyList.lastChild);
            }
        }
        
        // Load history on start
        fetch('/history').then(r => r.json()).then(data => {
            if (data.history) {
                data.history.forEach(h => addHistory(h.filename, h.timestamp));
            }
        });
    </script>
</body>
</html>
"""

# ─── KTP Crop Functions ───

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))


def detect_ktp(image):
    scale = 1.0
    h, w = image.shape[:2]
    max_dim = 1000
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
    resized = cv2.resize(image, None, fx=scale, fy=scale)

    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    image_area = resized.shape[0] * resized.shape[1]

    for contour in contours[:10]:
        area = cv2.contourArea(contour)
        if area < image_area * 0.05:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype("float32") / scale
            rect = order_points(pts)
            (tl, tr, br, bl) = rect
            width = np.linalg.norm(tr - tl)
            height = np.linalg.norm(bl - tl)
            if height == 0:
                continue
            if abs(width / height - KTP_ASPECT_RATIO) < 0.3:
                return rect
    return None


def enhance(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)


def crop_ktp(image):
    rect = detect_ktp(image)
    if rect is None:
        return None, "KTP tidak terdeteksi. Coba foto dari angle yang lebih frontal."
    
    cropped = four_point_transform(image, rect)
    cropped = enhance(cropped)
    cropped = cv2.resize(cropped, (OUTPUT_WIDTH, OUTPUT_HEIGHT), interpolation=cv2.INTER_LANCZOS4)
    return cropped, None


# ─── Routes ───

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/upload', methods=['POST'])
def upload():
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'Tidak ada foto yang diupload'})
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'File tidak valid'})
    
    # Read image
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if image is None:
        return jsonify({'success': False, 'error': 'Gagal membaca gambar'})
    
    # Crop KTP
    cropped, error = crop_ktp(image)
    
    if error:
        return jsonify({'success': False, 'error': error})
    
    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ktp_{ts}.jpg"
    output_path = OUTPUT_DIR / filename
    cv2.imwrite(str(output_path), cropped, [cv2.IMWRITE_JPEG_QUALITY, 95])
    
    timestamp = datetime.now().strftime("%d %b %Y, %H:%M")
    return jsonify({
        'success': True,
        'filename': filename,
        'timestamp': timestamp,
        'path': str(output_path)
    })


@app.route('/history')
def history():
    files = sorted(OUTPUT_DIR.glob("ktp_*.jpg"), reverse=True)[:10]
    history = []
    for f in files:
        ts = f.stem.replace("ktp_", "")
        try:
            dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
            timestamp = dt.strftime("%d %b %Y, %H:%M")
        except:
            timestamp = ts
        history.append({
            'filename': f.name,
            'timestamp': timestamp
        })
    return jsonify({'history': history})


@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory(str(OUTPUT_DIR), filename)


def get_local_ip():
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description="KTP Upload Server")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--open", action="store_true", help="Open browser automatically")
    args = parser.parse_args()
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    ip = get_local_ip()
    
    print()
    print("=" * 50)
    print("  📸 KTP Upload Server")
    print("=" * 50)
    print()
    print(f"  🌐 Buka di HP: http://{ip}:{args.port}")
    print(f"  💻 Buka di PC:  http://localhost:{args.port}")
    print()
    print(f"  📁 Foto tersimpan di: {OUTPUT_DIR}")
    print()
    print("-" * 50)
    print("  Tips:")
    print("  • Pastikan HP & komputer di WiFi yang sama")
    print("  • Buka browser di HP, ketik URL di atas")
    print("  • Foto KTP, langsung ter-crop otomatis!")
    print("=" * 50)
    print()
    
    if args.open:
        import webbrowser
        webbrowser.open(f"http://localhost:{args.port}")
    
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
