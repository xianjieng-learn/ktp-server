#!/usr/bin/env python3
"""
KTP Upload Server
=================
Foto KTP di HP → Auto-Crop → Auto-Download di Komputer

Usage: python server.py
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

OUTPUT_DIR = Path(__file__).parent / "ktp_photos"
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── HTML untuk HP ───
HP_PAGE = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>KTP Upload</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0f172a;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}
.hdr{text-align:center;margin-bottom:25px}.hdr h1{font-size:22px}.hdr p{font-size:13px;color:#94a3b8;margin-top:4px}
.card{width:100%;max-width:380px;background:#1e293b;border-radius:16px;padding:24px}
.zone{border:2px dashed #475569;border-radius:12px;padding:30px;text-align:center;cursor:pointer}
.zone:hover{border-color:#3b82f6}.zone .ic{font-size:48px}.zone h3{font-size:16px;margin:8px 0 4px}.zone p{font-size:12px;color:#64748b}
.zone input{display:none}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;margin-top:12px}
.bp{background:#3b82f6;color:#fff}.bp:disabled{background:#475569}
.prev{margin-top:12px;display:none}.prev.show{display:block}.prev img{width:100%;border-radius:10px;border:2px solid #334155}
.prev .inf{font-size:11px;color:#64748b;text-align:center;margin-top:6px}
.st{padding:12px;border-radius:10px;font-size:13px;margin-top:12px;display:none}
.st.show{display:block}.st.ok{background:#064e3b;color:#6ee7b7}.st.err{background:#7f1d1d;color:#fca5a5}.st.inf{background:#1e3a5f;color:#93c5fd}
</style>
</head>
<body>
<div class="hdr"><h1>📸 KTP Upload</h1><p>Foto → Auto-Crop → Upload</p></div>
<div class="card">
<div class="zone" id="z"><div class="ic">📷</div><h3>Ketuk untuk Foto</h3><p>atau pilih dari galeri</p><input type="file" id="fi" accept="image/*" capture="environment"></div>
<div class="prev" id="pv"><img id="pi"><div class="inf" id="pn"></div></div>
<button class="btn bp" id="ub" disabled>📤 Upload & Crop</button>
<div class="st" id="st"></div>
</div>
<script>
const R=85.6/53.98,z=document.getElementById('z'),fi=document.getElementById('fi'),ub=document.getElementById('ub'),pv=document.getElementById('pv'),pi=document.getElementById('pi'),pn=document.getElementById('pn'),st=document.getElementById('st');
let sf=null;z.onclick=()=>fi.click();
fi.onchange=e=>{if(e.target.files[0]){sf=e.target.files[0];ub.disabled=false;const r=new FileReader();r.onload=e=>{pi.src=e.target.result;pn.textContent=sf.name;pv.classList.add('show')};r.readAsDataURL(sf)}};
ub.onclick=async()=>{if(!sf)return;ub.disabled=true;ub.textContent='⏳ Processing...';ss('inf','⏳ Cropping...');
try{const b=await ac(sf);if(!b){ss('err','❌ KTP tidak terdeteksi.');ub.disabled=false;ub.textContent='📤 Upload & Crop';return}
ss('inf','⏳ Uploading...');const fd=new FormData();fd.append('photo',b,'ktp.jpg');const r=await fetch('/upload',{method:'POST',body:fd});const j=await r.json();
if(j.success){ss('ok','✅ Berhasil! Cek komputer untuk download.');sf=null;fi.value='';pv.classList.remove('show')}else ss('err','❌ '+j.error)}catch(e){ss('err','❌ '+e.message)}
ub.disabled=false;ub.textContent='📤 Upload & Crop'};
async function ac(f){return new Promise(r=>{const i=new Image();i.onload=()=>{const c=document.createElement('canvas'),x=c.getContext('2d');c.width=i.width;c.height=i.height;x.drawImage(i,0,0);const d=x.getImageData(0,0,c.width,c.height).data,g=new Uint8Array(c.width*c.height);
for(let j=0;j<g.length;j++){const k=j*4;g[j]=(d[k]*.299+d[k+1]*.587+d[k+2]*.114)|0}
const e=new Uint8Array(c.width*c.height);for(let y=1;y<c.height-1;y++)for(let xx=1;xx<c.width-1;xx++){const idx=y*c.width+xx;
const gx=-g[(y-1)*c.width+xx-1]+g[(y-1)*c.width+xx+1]-2*g[y*c.width+xx-1]+2*g[y*c.width+xx+1]-g[(y+1)*c.width+xx-1]+g[(y+1)*c.width+xx+1];
const gy=-g[(y-1)*c.width+xx-1]-2*g[(y-1)*c.width+xx]-g[(y-1)*c.width+xx+1]+g[(y+1)*c.width+xx-1]+2*g[(y+1)*c.width+xx]+g[(y+1)*c.width+xx+1];
e[idx]=Math.min(255,Math.sqrt(gx*gx+gy*gy))|0}
let mnx=c.width,mxx=0,mny=c.height,mxy=0,ec=0;for(let y=0;y<c.height;y++)for(let xx=0;xx<c.width;xx++)if(e[y*c.width+xx]>50){mnx=Math.min(mnx,xx);mxx=Math.max(mxx,xx);mny=Math.min(mny,y);mxy=Math.max(mxy,y);ec++}
if(ec<c.width*c.height*.01){r(null);return}const p=20;mnx=Math.max(0,mnx-p);mny=Math.max(0,mny-p);mxx=Math.min(c.width-1,mxx+p);mxy=Math.min(c.height-1,mxy+p);
let cw=mxx-mnx,ch=mxy-mny;if(Math.abs(cw/ch-R)>.3)ch=cw/R;
const oc=document.createElement('canvas'),ow=1200,oh=Math.round(ow/R);oc.width=ow;oc.height=oh;oc.getContext('2d').drawImage(c,mnx,mny,cw,ch,0,0,ow,oh);oc.toBlob(b=>r(b),'image/jpeg',.92)};i.src=URL.createObjectURL(f)})}
function ss(t,m){st.className='st show '+t;st.textContent=m}
</script>
</body></html>"""

# ─── HTML untuk Komputer (Gallery + Auto-Download) ───
PC_PAGE = r"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>KTP Photos - Auto Download</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#f8fafc;color:#1e293b;padding:30px}
.hdr{margin-bottom:20px}.hdr h1{font-size:24px}.hdr p{font-size:14px;color:#64748b;margin-top:4px}
.qr-box{background:#1e293b;border-radius:16px;padding:20px;margin-bottom:20px;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
.qr-box .txt{color:#fff}.qr-box .txt h2{font-size:16px;margin-bottom:4px}.qr-box .txt p{font-size:12px;color:#94a3b8}
.qr-box img{width:120px;height:120px;background:#fff;border-radius:10px;padding:8px}
.status-bar{background:#fff;border-radius:12px;padding:16px;margin-bottom:20px;display:flex;align-items:center;gap:12px;box-shadow:0 1px 3px rgba(0,0,0,.1)}
.status-bar .dot{width:10px;height:10px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.status-bar .txt{font-size:14px;font-weight:500}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.card{background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);animation:slideIn .3s ease}
@keyframes slideIn{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.card.new{border:2px solid #22c55e}
.card img{width:100%;height:160px;object-fit:cover;cursor:pointer}
.card .inf{padding:10px 14px;display:flex;justify-content:space-between;align-items:center}
.card .nm{font-size:12px;font-weight:500}.card .tm{font-size:10px;color:#94a3b8}
.card .dl{display:inline-block;background:#3b82f6;color:#fff;text-decoration:none;padding:5px 12px;border-radius:6px;font-size:11px;font-weight:500}
.card .dl:hover{background:#2563eb}
.empty{text-align:center;padding:60px;color:#94a3b8}.empty .ic{font-size:48px;margin-bottom:12px}
.badge{position:absolute;top:8px;right:8px;background:#22c55e;color:#fff;font-size:10px;padding:3px 8px;border-radius:10px;font-weight:600}
</style>
</head>
<body>
<div class="hdr"><h1>📸 KTP Photos</h1><p>Upload dari HP, auto-muncul di sini</p></div>
<div class="qr-box">
<div class="txt"><h2>📱 Scan dari HP</h2><p>Buka kamera HP → Scan QR → Foto KTP</p><p style="margin-top:4px;font-size:11px;color:#64748b">%%HP_URL%%</p></div>
<img src="%%QR_URL%%" alt="QR">
</div>
<div class="status-bar">
<div class="dot"></div>
<div class="txt">🟢 Auto-refresh aktif — foto baru langsung muncul</div>
</div>
<div class="grid" id="grid">%%ITEMS%%</div>
<script>
// Auto-refresh setiap 2 detik
let lastCount = %%COUNT%%;
setInterval(async()=>{
try{
const r=await fetch('/api/files');const d=await r.json();
if(d.count>lastCount){
// Ada file baru!
lastCount=d.count;
document.getElementById('grid').innerHTML=d.html;
// Play sound
try{new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdH+Jk42HfnR1gIqWlJOEe3Z4h5SVk4N8d3qJlZSTg3x4e4qVlJODfHh8i5WUk4N9eX2LlZSTg315fouVlJODfXp+i5WUk4N+en+LlZSTg357f4uVlJODfnt/i5WUk4N+fICLlZSTg358gIuVlJODfnyAi5WUk4N+fYCLlZSTg359gIuVlJODfn2Ai5WUk4N+fYCLlZSTg359gIuVlJODfn2Ai5WUk4N+fYCLlZQ=' type='audio/wav}');
// Show notification
if(Notification.permission==='granted'){new Notification('KTP Baru! 📸',{body:'Foto KTP baru tersimpan',icon:'📷'})}
}
// Update grid
document.getElementById('grid').innerHTML=d.html;
}catch(e){}
},2000);
// Request notification permission
if('Notification'in window&&Notification.permission==='default'){Notification.requestPermission()}
</script>
</body></html>"""


class KTPHandler(http.server.BaseHTTPRequestHandler):
    last_count = 0

    def do_GET(self):
        if self.path in ('/', '/hp'):
            self._html(HP_PAGE)
        elif self.path == '/pc':
            files = sorted(OUTPUT_DIR.glob("ktp_*.jpg"), reverse=True)
            ip = get_local_ip()
            hp_url = f"http://{ip}:{self.server.server_address[1]}/hp"
            qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={hp_url}"
            items = self._build_items(files, new_set=False)
            page = PC_PAGE.replace("%%ITEMS%%", items).replace("%%COUNT%%", str(len(files))) \
                .replace("%%HP_URL%%", hp_url).replace("%%QR_URL%%", qr_api)
            self._html(page)
        elif self.path == '/api/files':
            files = sorted(OUTPUT_DIR.glob("ktp_*.jpg"), reverse=True)
            items = self._build_items(files, new_set=True)
            self._json({"count": len(files), "html": items})
        elif self.path.startswith('/photo/') or self.path.startswith('/download/'):
            fname = self.path.split('/')[-1]
            fpath = OUTPUT_DIR / fname
            if fpath.exists():
                self.send_response(200)
                if self.path.startswith('/download/'):
                    self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
                self.send_header('Content-Type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(fpath.read_bytes())
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/upload':
            try:
                ct = self.headers.get('Content-Type', '')
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': ct})
                item = form['photo']
                if item.filename:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fn = f"ktp_{ts}.jpg"
                    (OUTPUT_DIR / fn).write_bytes(item.file.read())
                    self._json({"success": True, "filename": fn})
                else:
                    self.send_error(400)
            except Exception as e:
                self._json({"success": False, "error": str(e)})
        else:
            self.send_error(404)

    def _build_items(self, files, new_set=False):
        items = ""
        for i, f in enumerate(files):
            ts = f.stem.replace("ktp_", "")
            try: t = datetime.strptime(ts, "%Y%m%d_%H%M%S").strftime("%d %b %Y, %H:%M")
            except: t = ts
            cls = "card new" if (new_set and i == 0) else "card"
            items += f'<div class="{cls}"><img src="/photo/{f.name}" onclick="window.open(\'/photo/{f.name}\')"><div class="inf"><div><div class="nm">{f.name}</div><div class="tm">{t}</div></div><a class="dl" href="/download/{f.name}">📥 Download</a></div></div>'
        if not items:
            items = '<div class="empty"><div class="ic">📭</div><p>Belum ada foto KTP</p><p style="font-size:12px;margin-top:8px">Upload dari HP dulu!</p></div>'
        return items

    def _html(self, content):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, *args):
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
    hp_url = f"http://{ip}:{args.port}/hp"

    print()
    print("=" * 50)
    print("  📸 KTP Upload Server (Auto-Download)")
    print("=" * 50)
    print()
    print(f"  📱 HP: {hp_url}")
    print(f"  💻 PC: http://localhost:{args.port}/pc")
    print()
    print("-" * 50)
    print("  1. Buka /pc di komputer")
    print("  2. Scan QR dari HP")
    print("  3. Foto KTP → Auto-Crop → Upload")
    print("  4. Komputer langsung muncul foto baru!")
    print("=" * 50)
    print()

    with socketserver.TCPServer(("0.0.0.0", args.port), KTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  👋 Stopped.")


if __name__ == "__main__":
    main()
