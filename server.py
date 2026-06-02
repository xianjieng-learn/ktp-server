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
.card{width:100%;max-width:380px;background:#1e293b;border-radius:16px;padding:24px;overflow:hidden}
.zone{border:2px dashed #475569;border-radius:12px;padding:30px;text-align:center;cursor:pointer}
.zone:hover{border-color:#3b82f6}.zone .ic{font-size:48px}.zone h3{font-size:16px;margin:8px 0 4px}.zone p{font-size:12px;color:#64748b}
.zone input{display:none}
/* Camera container */
.cam-wrap{display:none;position:relative;width:100%;border-radius:12px;overflow:hidden;background:#000;animation:fi .3s ease}
.cam-wrap.show{display:block}
@keyframes fi{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
.cam-wrap video{width:100%;display:block;border-radius:12px;object-fit:cover}
/* KTP guide overlay */
.guide-overlay{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;pointer-events:none;z-index:2}
.guide-frame{position:relative;width:82%;aspect-ratio:1.586/1;border:2px solid rgba(255,255,255,.8);border-radius:4px;box-shadow:0 0 0 9999px rgba(0,0,0,.55)}
/* Corner marks */
.corner-mark{position:absolute;width:22px;height:22px;pointer-events:none}
.corner-mark::before,.corner-mark::after{content:'';position:absolute;background:rgba(255,255,255,.9)}
.corner-mark::before{width:3px;height:22px}
.corner-mark::after{width:22px;height:3px}
.corner-mark.tl{top:-2px;left:-2px}.corner-mark.tl::before{top:0;left:0}.corner-mark.tl::after{top:0;left:0}
.corner-mark.tr{top:-2px;right:-2px}.corner-mark.tr::before{top:0;right:0}.corner-mark.tr::after{top:0;right:0}
.corner-mark.bl{bottom:-2px;left:-2px}.corner-mark.bl::before{bottom:0;left:0}.corner-mark.bl::after{bottom:0;left:0}
.corner-mark.br{bottom:-2px;right:-2px}.corner-mark.br::before{bottom:0;right:0}.corner-mark.br::after{bottom:0;right:0}
/* Guide text */
.guide-text{position:absolute;bottom:-24px;left:50%;transform:translateX(-50%);font-size:11px;color:rgba(255,255,255,.85);white-space:nowrap;text-shadow:0 1px 3px rgba(0,0,0,.7);pointer-events:none}
/* Close button */
.close-btn{position:absolute;top:8px;right:8px;z-index:5;background:rgba(0,0,0,.6);color:#fff;border:none;border-radius:20px;padding:6px 12px;font-size:12px;cursor:pointer;display:flex;align-items:center;gap:4px;backdrop-filter:blur(4px)}
.close-btn:hover{background:rgba(0,0,0,.8)}
/* Camera controls */
.cam-ctrl{display:none;flex-direction:column;align-items:center;padding:16px 0 8px;gap:10px}
.cam-ctrl.show{display:flex;animation:fi .3s ease}
.cap-btn{width:64px;height:64px;border-radius:50%;border:4px solid #fff;background:transparent;cursor:pointer;position:relative;transition:transform .15s;padding:0}
.cap-btn:active{transform:scale(.9)}
.cap-btn::after{content:'';position:absolute;top:6px;left:6px;right:6px;bottom:6px;border-radius:50%;background:#ef4444;transition:background .15s}
.cap-btn:active::after{background:#dc2626}
.gallink{font-size:12px;color:#94a3b8;cursor:pointer;background:none;border:none;text-decoration:underline;padding:4px 8px}
.gallink:hover{color:#cbd5e1}
.btn{width:100%;padding:14px;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;margin-top:12px}
.bp{background:#3b82f6;color:#fff}.bp:disabled{background:#475569}
.prev{margin-top:12px;display:none}.prev.show{display:block}.prev img{width:100%;border-radius:10px;border:2px solid #334155}
.prev .inf{font-size:11px;color:#64748b;text-align:center;margin-top:6px}
.st{padding:12px;border-radius:10px;font-size:13px;margin-top:12px;display:none}
.st.show{display:block}.st.ok{background:#064e3b;color:#6ee7b7}.st.err{background:#7f1d1d;color:#fca5a5}.st.inf{background:#1e3a5f;color:#93c5fd}
#captureCanvas{display:none}
</style>
</head>
<body>
<div class="hdr"><h1>📸 KTP Upload</h1><p>Foto → Auto-Crop → Upload</p></div>
<div class="card">
<!-- Upload zone -->
<div class="zone" id="z"><div class="ic">📷</div><h3>Ketuk untuk Foto</h3><p>atau pilih dari galeri</p><input type="file" id="fi" accept="image/*"></div>
<!-- Camera viewfinder -->
<div class="cam-wrap" id="cw">
<button class="close-btn" id="clb">✕ Tutup</button>
<video id="cv" autoplay playsinline></video>
<div class="guide-overlay"><div class="guide-frame">
<div class="corner-mark tl"></div><div class="corner-mark tr"></div>
<div class="corner-mark bl"></div><div class="corner-mark br"></div>
<span class="guide-text">Posisikan KTP di area ini</span>
</div></div>
</div>
<!-- Camera controls -->
<div class="cam-ctrl" id="cc">
<button class="cap-btn" id="capb" title="Ambil Foto"></button>
<button class="gallink" id="glb">atau pilih dari galeri</button>
</div>
<div class="prev" id="pv"><img id="pi"><div class="inf" id="pn"></div></div>
<button class="btn bp" id="ub" disabled>📤 Upload & Crop</button>
<div class="st" id="st"></div>
</div>
<canvas id="captureCanvas"></canvas>
<input type="file" id="galInput" accept="image/*" style="display:none">
<script>
const R=85.6/53.98;
const z=document.getElementById('z'),fi=document.getElementById('fi'),ub=document.getElementById('ub'),pv=document.getElementById('pv'),pi=document.getElementById('pi'),pn=document.getElementById('pn'),st=document.getElementById('st');
const cw=document.getElementById('cw'),cv=document.getElementById('cv'),cc=document.getElementById('cc'),capb=document.getElementById('capb'),clb=document.getElementById('clb'),glb=document.getElementById('glb'),galInput=document.getElementById('galInput'),capCanvas=document.getElementById('captureCanvas');
let sf=null,camStream=null;
// Upload zone click → open camera
z.onclick=()=>openCam();
// Gallery input
glb.onclick=e=>{e.stopPropagation();galInput.click()};
fi.onchange=e=>{if(e.target.files[0]){handleFile(e.target.files[0])}};
galInput.onchange=e=>{if(e.target.files[0]){stopCam();handleFile(e.target.files[0])}};
function handleFile(f){sf=f;ub.disabled=false;const r=new FileReader();r.onload=e=>{pi.src=e.target.result;pn.textContent=f.name;pv.classList.add('show')};r.readAsDataURL(f)}
// Camera functions
async function openCam(){
if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){ss('err','⚠️ Kamera tidak didukung.');fi.click();return}
try{
const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment',width:{ideal:1920},height:{ideal:1080}},audio:false});
camStream=stream;cv.srcObject=stream;
z.style.display='none';cw.classList.add('show');cc.classList.add('show');
pv.classList.remove('show');ub.disabled=true;st.className='st';
}catch(e){console.warn('getUserMedia failed:',e);ss('err','⚠️ Tidak bisa akses kamera.');fi.click()}
}
function stopCam(){
if(camStream){camStream.getTracks().forEach(t=>t.stop());camStream=null}
cv.srcObject=null;cw.classList.remove('show');cc.classList.remove('show');z.style.display=''
}
clb.onclick=e=>{e.stopPropagation();stopCam()};
// Capture photo
capb.onclick=e=>{
e.stopPropagation();if(!camStream)return;
capCanvas.width=cv.videoWidth;capCanvas.height=cv.videoHeight;
capCanvas.getContext('2d').drawImage(cv,0,0,capCanvas.width,capCanvas.height);
stopCam();
capCanvas.toBlob(function(blob){
if(!blob){ss('err','❌ Gagal mengambil foto.');return}
const f=new File([blob],'ktp_capture_'+Date.now()+'.jpg',{type:'image/jpeg'});
handleFile(f);
},'image/jpeg',.95)
};
// Upload & Crop button
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
window.addEventListener('beforeunload',stopCam);
document.addEventListener('visibilitychange',()=>{if(document.hidden&&camStream)stopCam()});
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
.cam-btn{background:#3b82f6;color:#fff;border:none;border-radius:10px;padding:12px 20px;font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:8px;transition:background .2s}
.cam-btn:hover{background:#2563eb}
.cam-btn:active{transform:scale(.97)}
.cam-section{display:none;position:relative;background:#000;border-radius:16px;overflow:hidden;margin-bottom:20px;animation:camIn .3s ease;min-height:240px}
.cam-section.show{display:block}
@keyframes camIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}
.cam-section video{width:100%;display:block;border-radius:16px;object-fit:cover;min-height:240px;background:#111}
.guide-overlay{position:absolute;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;pointer-events:none;z-index:2}
.guide-frame{position:relative;width:82%;aspect-ratio:1.586/1;border:2px solid rgba(255,255,255,.8);border-radius:4px;box-shadow:0 0 0 9999px rgba(0,0,0,.55)}
.corner-mark{position:absolute;width:22px;height:22px;pointer-events:none}
.corner-mark::before,.corner-mark::after{content:'';position:absolute;background:rgba(255,255,255,.9)}
.corner-mark::before{width:3px;height:22px}
.corner-mark::after{width:22px;height:3px}
.corner-mark.tl{top:-2px;left:-2px}.corner-mark.tl::before{top:0;left:0}.corner-mark.tl::after{top:0;left:0}
.corner-mark.tr{top:-2px;right:-2px}.corner-mark.tr::before{top:0;right:0}.corner-mark.tr::after{top:0;right:0}
.corner-mark.bl{bottom:-2px;left:-2px}.corner-mark.bl::before{bottom:0;left:0}.corner-mark.bl::after{bottom:0;left:0}
.corner-mark.br{bottom:-2px;right:-2px}.corner-mark.br::before{bottom:0;right:0}.corner-mark.br::after{bottom:0;right:0}
.guide-text{position:absolute;bottom:-24px;left:50%;transform:translateX(-50%);font-size:11px;color:rgba(255,255,255,.85);white-space:nowrap;text-shadow:0 1px 3px rgba(0,0,0,.7);pointer-events:none}
.close-cam{position:absolute;top:10px;right:10px;z-index:5;background:rgba(0,0,0,.6);color:#fff;border:none;border-radius:20px;padding:6px 14px;font-size:12px;cursor:pointer;display:flex;align-items:center;gap:4px;backdrop-filter:blur(4px)}
.close-cam:hover{background:rgba(0,0,0,.8)}
.cam-controls{display:flex;align-items:center;justify-content:center;padding:16px 0;gap:20px}
.cap-btn{width:64px;height:64px;border-radius:50%;border:4px solid #fff;background:transparent;cursor:pointer;position:relative;transition:transform .15s;padding:0}
.cap-btn:active{transform:scale(.9)}
.cap-btn::after{content:'';position:absolute;top:6px;left:6px;right:6px;bottom:6px;border-radius:50%;background:#ef4444;transition:background .15s}
.cap-btn:active::after{background:#dc2626}
.cam-status{color:#fff;font-size:13px;text-align:center;padding:0 0 10px}
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
#pcCapCanvas{display:none}
.upload-toast{position:fixed;top:20px;right:20px;background:#064e3b;color:#6ee7b7;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:500;z-index:999;animation:slideIn .3s ease;display:none}
.upload-toast.show{display:block}
.upload-toast.err{background:#7f1d1d;color:#fca5a5}
</style>
</head>
<body>
<div class="hdr"><h1>📸 KTP Photos</h1><p>Upload dari HP atau langsung dari webcam komputer</p></div>
<div class="qr-box">
<div class="txt"><h2>📱 Scan dari HP</h2><p>Buka kamera HP → Scan QR → Foto KTP</p><p style="margin-top:4px;font-size:11px;color:#64748b">%%HP_URL%%</p></div>
<img src="%%QR_URL%%" alt="QR">
<button class="cam-btn" onclick="openPCWebcam()">📷 Foto dari Webcam</button>
</div>
<div class="cam-section" id="pcCamSection">
<video id="pcCamVideo" autoplay playsinline></video>
<div class="guide-overlay"><div class="guide-frame">
<div class="corner-mark tl"></div><div class="corner-mark tr"></div>
<div class="corner-mark bl"></div><div class="corner-mark br"></div>
<span class="guide-text">Posisikan KTP di area ini</span>
</div></div>
<button class="close-cam" onclick="stopPCWebcam()">✕ Tutup</button>
<div class="cam-controls">
<button class="cap-btn" id="pcCapBtn" title="Ambil Foto"></button>
</div>
<div class="cam-status" id="pcCamStatus"></div>
</div>
<canvas id="pcCapCanvas"></canvas>
<div class="upload-toast" id="pcToast"></div>
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
lastCount=d.count;
document.getElementById('grid').innerHTML=d.html;
try{new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdH+Jk42HfnR1gIqWlJOEe3Z4h5SVk4N8d3qJlZSTg3x4e4qVlJODfHh8i5WUk4N9eX2LlZSTg315fouVlJODfXp+i5WUk4N+en+LlZSTg357f4uVlJODfnt/i5WUk4N+fICLlZSTg358gIuVlJODfnyAi5WUk4N+fYCLlZSTg359gIuVlJODfn2Ai5WUk4N+fYCLlZSTg359gIuVlJODfn2Ai5WUk4N+fYCLlZQ=' type='audio/wav}');
if(Notification.permission==='granted'){new Notification('KTP Baru! 📸',{body:'Foto KTP baru tersimpan',icon:'📷'})}
}
document.getElementById('grid').innerHTML=d.html;
}catch(e){}
},2000);
if('Notification'in window&&Notification.permission==='default'){Notification.requestPermission()}

// === Webcam Capture ===
const R=85.6/53.98;
let pcCamStream=null;
const pcCamSection=document.getElementById('pcCamSection');
const pcCamVideo=document.getElementById('pcCamVideo');
const pcCapCanvas=document.getElementById('pcCapCanvas');
const pcCapBtn=document.getElementById('pcCapBtn');
const pcToast=document.getElementById('pcToast');
const pcCamStatus=document.getElementById('pcCamStatus');

function pcToastMsg(msg,err){
pcToast.textContent=msg;pcToast.className='upload-toast show'+(err?' err':'');
setTimeout(()=>{pcToast.className='upload-toast'},3000);
}

async function openPCWebcam(){
console.log('openPCWebcam called, mediaDevices:',!!navigator.mediaDevices);
if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){
console.error('getUserMedia not supported');
pcToastMsg('⚠️ Kamera tidak didukung. Pastikan akses via localhost (bukan IP LAN) dan pakai Chrome/Firefox.',true);return}
try{
const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:{ideal:1280},height:{ideal:720}},audio:false});
pcCamStream=stream;pcCamVideo.srcObject=stream;
pcCamSection.classList.add('show');
pcCamStatus.textContent='🎥 Kamera aktif — posisikan KTP lalu tekan tombol merah';
}catch(e){console.warn('getUserMedia failed:',e);
pcToastMsg('⚠️ Kamera gagal: '+e.message+'. Coba pakai localhost.',true)}
}

function stopPCWebcam(){
if(pcCamStream){pcCamStream.getTracks().forEach(t=>t.stop());pcCamStream=null}
pcCamVideo.srcObject=null;pcCamSection.classList.remove('show');
}

pcCapBtn.onclick=async()=>{
if(!pcCamStream)return;
pcCapCanvas.width=pcCamVideo.videoWidth;
pcCapCanvas.height=pcCamVideo.videoHeight;
pcCapCanvas.getContext('2d').drawImage(pcCamVideo,0,0,pcCapCanvas.width,pcCapCanvas.height);
stopPCWebcam();
pcCamStatus.textContent='';
pcToastMsg('⏳ Memproses foto...');
pcCapCanvas.toBlob(async function(blob){
if(!blob){pcToastMsg('❌ Gagal mengambil foto.',true);return}
try{
const cropped=await autoCropKTP(blob);
if(!cropped){pcToastMsg('❌ KTP tidak terdeteksi. Coba lagi dengan posisi yang lebih jelas.',true);return}
pcToastMsg('⏳ Uploading...');
const fd=new FormData();fd.append('photo',cropped,'ktp.jpg');
const r=await fetch('/upload',{method:'POST',body:fd});
const j=await r.json();
if(j.success){pcToastMsg('✅ Berhasil! Foto akan muncul di bawah.')}
else{pcToastMsg('❌ '+j.error,true)}
}catch(e){pcToastMsg('❌ '+e.message,true)}
},'image/jpeg',.95);
};

// Auto-crop KTP (same algorithm as HP page)
function autoCropKTP(file){return new Promise(resolve=>{
const i=new Image();i.onload=()=>{
const c=document.createElement('canvas'),x=c.getContext('2d');
c.width=i.width;c.height=i.height;x.drawImage(i,0,0);
const d=x.getImageData(0,0,c.width,c.height).data;
const g=new Uint8Array(c.width*c.height);
for(let j=0;j<g.length;j++){const k=j*4;g[j]=(d[k]*.299+d[k+1]*.587+d[k+2]*.114)|0}
const e=new Uint8Array(c.width*c.height);
for(let y=1;y<c.height-1;y++)for(let xx=1;xx<c.width-1;xx++){
const idx=y*c.width+xx;
const gx=-g[(y-1)*c.width+xx-1]+g[(y-1)*c.width+xx+1]-2*g[y*c.width+xx-1]+2*g[y*c.width+xx+1]-g[(y+1)*c.width+xx-1]+g[(y+1)*c.width+xx+1];
const gy=-g[(y-1)*c.width+xx-1]-2*g[(y-1)*c.width+xx]-g[(y-1)*c.width+xx+1]+g[(y+1)*c.width+xx-1]+2*g[(y+1)*c.width+xx]+g[(y+1)*c.width+xx+1];
e[idx]=Math.min(255,Math.sqrt(gx*gx+gy*gy))|0}
let mnx=c.width,mxx=0,mny=c.height,mxy=0,ec=0;
for(let y=0;y<c.height;y++)for(let xx=0;xx<c.width;xx++)if(e[y*c.width+xx]>50){mnx=Math.min(mnx,xx);mxx=Math.max(mxx,xx);mny=Math.min(mny,y);mxy=Math.max(mxy,y);ec++}
if(ec<c.width*c.height*.01){resolve(null);return}
const p=20;mnx=Math.max(0,mnx-p);mny=Math.max(0,mny-p);mxx=Math.min(c.width-1,mxx+p);mxy=Math.min(c.height-1,mxy+p);
let cw=mxx-mnx,ch=mxy-mny;if(Math.abs(cw/ch-R)>.3)ch=cw/R;
const oc=document.createElement('canvas'),ow=1200,oh=Math.round(ow/R);
oc.width=ow;oc.height=oh;oc.getContext('2d').drawImage(c,mnx,mny,cw,ch,0,0,ow,oh);
oc.toBlob(b=>resolve(b),'image/jpeg',.92)};
i.src=URL.createObjectURL(file)});
}

window.addEventListener('beforeunload',stopPCWebcam);
document.addEventListener('visibilitychange',()=>{if(document.hidden&&pcCamStream)stopPCWebcam()});
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
    print("  2. Scan QR dari HP ATAU klik 'Foto dari Webcam'")
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
