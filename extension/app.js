const KTP_RATIO = 85.6 / 53.98;
const OUTPUT_WIDTH = 1200;
const OUTPUT_FOLDER = 'Hasil KTP';

const el = (id) => document.getElementById(id);
const uploadZone = el('uploadZone');
const fileInput = el('fileInput');
const cameraBox = el('cameraBox');
const cameraVideo = el('cameraVideo');
const cameraControls = el('cameraControls');
const closeCamera = el('closeCamera');
const captureButton = el('captureButton');
const pickGallery = el('pickGallery');
const captureCanvas = el('captureCanvas');
const previewBox = el('previewBox');
const previewImage = el('previewImage');
const previewInfo = el('previewInfo');
const cropButton = el('cropButton');
const resetButton = el('resetButton');
const statusBox = el('statusBox');

let selectedFile = null;
let cameraStream = null;
let lastObjectUrl = null;

uploadZone.addEventListener('click', openCamera);
pickGallery.addEventListener('click', () => fileInput.click());
closeCamera.addEventListener('click', stopCamera);
captureButton.addEventListener('click', captureFromCamera);
fileInput.addEventListener('change', (event) => {
  const file = event.target.files && event.target.files[0];
  if (file) {
    stopCamera();
    setSelectedFile(file);
  }
});
cropButton.addEventListener('click', cropAndDownload);
resetButton.addEventListener('click', resetAll);
window.addEventListener('beforeunload', stopCamera);
document.addEventListener('visibilitychange', () => {
  if (document.hidden && cameraStream) stopCamera();
});

async function openCamera() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setStatus('err', '⚠️ Kamera tidak didukung. Pilih foto dari galeri saja.');
    fileInput.click();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: 'environment' },
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: false
    });
    cameraStream = stream;
    cameraVideo.srcObject = stream;
    uploadZone.style.display = 'none';
    cameraBox.classList.add('show');
    cameraControls.classList.add('show');
    previewBox.classList.remove('show');
    cropButton.disabled = true;
    setStatus('', '');
  } catch (error) {
    console.warn('Kamera gagal:', error);
    setStatus('err', '⚠️ Tidak bisa akses kamera. Cek permission Chrome, atau pilih dari galeri.');
    fileInput.click();
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
  cameraVideo.srcObject = null;
  cameraBox.classList.remove('show');
  cameraControls.classList.remove('show');
  uploadZone.style.display = '';
}

function captureFromCamera() {
  if (!cameraStream || !cameraVideo.videoWidth) return;
  captureCanvas.width = cameraVideo.videoWidth;
  captureCanvas.height = cameraVideo.videoHeight;
  captureCanvas.getContext('2d').drawImage(cameraVideo, 0, 0, captureCanvas.width, captureCanvas.height);
  stopCamera();
  captureCanvas.toBlob((blob) => {
    if (!blob) {
      setStatus('err', '❌ Gagal mengambil foto.');
      return;
    }
    const file = new File([blob], `ktp_capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
    setSelectedFile(file);
  }, 'image/jpeg', 0.95);
}

function setSelectedFile(file) {
  selectedFile = file;
  cropButton.disabled = false;
  if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
  lastObjectUrl = URL.createObjectURL(file);
  previewImage.src = lastObjectUrl;
  previewInfo.textContent = `${file.name} • ${formatBytes(file.size)}`;
  previewBox.classList.add('show');
  setStatus('info', 'Siap dicrop. Kalau posisi kurang pas, foto ulang.');
}

async function cropAndDownload() {
  if (!selectedFile) return;
  cropButton.disabled = true;
  cropButton.textContent = '⏳ Cropping...';
  setStatus('info', '⏳ Mencari tepi KTP...');

  try {
    const blob = await autoCropKtp(selectedFile);
    if (!blob) {
      setStatus('err', '❌ KTP tidak terdeteksi. Coba foto ulang lebih terang dan seluruh KTP masuk frame.');
      return;
    }

    const dataUrl = await blobToDataUrl(blob);
    const filename = `${OUTPUT_FOLDER}/${buildFilename()}.jpg`;
    await chrome.downloads.download({ url: dataUrl, filename, saveAs: false });
    setStatus('ok', `✅ Berhasil disimpan: Downloads/${filename}`);
    selectedFile = null;
    fileInput.value = '';
  } catch (error) {
    console.error(error);
    setStatus('err', `❌ ${error.message || error}`);
  } finally {
    cropButton.disabled = !selectedFile;
    cropButton.textContent = '✂️ Crop & Download';
  }
}

async function autoCropKtp(file) {
  const image = await loadImage(file);
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  canvas.width = image.naturalWidth || image.width;
  canvas.height = image.naturalHeight || image.height;
  ctx.drawImage(image, 0, 0);
  URL.revokeObjectURL(image.src);

  const { data, width, height } = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const gray = new Uint8Array(width * height);
  for (let i = 0; i < gray.length; i++) {
    const j = i * 4;
    gray[i] = (data[j] * 0.299 + data[j + 1] * 0.587 + data[j + 2] * 0.114) | 0;
  }

  const edge = new Uint8Array(width * height);
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = y * width + x;
      const gx = -gray[(y - 1) * width + x - 1] + gray[(y - 1) * width + x + 1]
        - 2 * gray[y * width + x - 1] + 2 * gray[y * width + x + 1]
        - gray[(y + 1) * width + x - 1] + gray[(y + 1) * width + x + 1];
      const gy = -gray[(y - 1) * width + x - 1] - 2 * gray[(y - 1) * width + x] - gray[(y - 1) * width + x + 1]
        + gray[(y + 1) * width + x - 1] + 2 * gray[(y + 1) * width + x] + gray[(y + 1) * width + x + 1];
      edge[idx] = Math.min(255, Math.sqrt(gx * gx + gy * gy)) | 0;
    }
  }

  let minX = width;
  let maxX = 0;
  let minY = height;
  let maxY = 0;
  let edgeCount = 0;
  const threshold = 50;
  const marginX = Math.round(width * 0.03);
  const marginY = Math.round(height * 0.03);

  for (let y = marginY; y < height - marginY; y++) {
    for (let x = marginX; x < width - marginX; x++) {
      if (edge[y * width + x] > threshold) {
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minY = Math.min(minY, y);
        maxY = Math.max(maxY, y);
        edgeCount++;
      }
    }
  }

  if (edgeCount < width * height * 0.01 || maxX <= minX || maxY <= minY) return null;

  const pad = Math.round(Math.min(width, height) * 0.025);
  minX = Math.max(0, minX - pad);
  minY = Math.max(0, minY - pad);
  maxX = Math.min(width - 1, maxX + pad);
  maxY = Math.min(height - 1, maxY + pad);

  let cropW = maxX - minX;
  let cropH = maxY - minY;
  const currentRatio = cropW / cropH;
  if (Math.abs(currentRatio - KTP_RATIO) > 0.05) {
    if (currentRatio > KTP_RATIO) {
      const targetH = cropW / KTP_RATIO;
      const delta = targetH - cropH;
      minY = Math.max(0, minY - delta / 2);
      maxY = Math.min(height, maxY + delta / 2);
    } else {
      const targetW = cropH * KTP_RATIO;
      const delta = targetW - cropW;
      minX = Math.max(0, minX - delta / 2);
      maxX = Math.min(width, maxX + delta / 2);
    }
  }

  cropW = maxX - minX;
  cropH = maxY - minY;
  const out = document.createElement('canvas');
  out.width = OUTPUT_WIDTH;
  out.height = Math.round(OUTPUT_WIDTH / KTP_RATIO);
  out.getContext('2d').drawImage(canvas, minX, minY, cropW, cropH, 0, 0, out.width, out.height);
  return new Promise((resolve) => out.toBlob(resolve, 'image/jpeg', 0.92));
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('Gambar tidak bisa dibuka.'));
    image.src = URL.createObjectURL(file);
  });
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Gagal membuat file download.'));
    reader.readAsDataURL(blob);
  });
}

function buildFilename() {
  const now = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `ktp_${now.getFullYear()}${p(now.getMonth() + 1)}${p(now.getDate())}_${p(now.getHours())}${p(now.getMinutes())}${p(now.getSeconds())}`;
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB'];
  const exp = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, exp)).toFixed(exp ? 1 : 0)} ${units[exp]}`;
}

function setStatus(type, message) {
  if (!type || !message) {
    statusBox.className = 'status';
    statusBox.textContent = '';
    return;
  }
  statusBox.className = `status show ${type}`;
  statusBox.textContent = message;
}

function resetAll() {
  stopCamera();
  selectedFile = null;
  fileInput.value = '';
  previewBox.classList.remove('show');
  cropButton.disabled = true;
  cropButton.textContent = '✂️ Crop & Download';
  if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
  lastObjectUrl = null;
  setStatus('', '');
}
