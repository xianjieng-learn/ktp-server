const DOC_MODES = {
  ktp: { label: 'KTP', icon: '📷', ratio: 85.6 / 53.98, outputWidth: 1200, folder: 'Hasil KTP', prefix: 'ktp' },
  sktm: { label: 'SKTM', icon: '📄', ratio: 210 / 297, outputWidth: 1240, folder: 'Hasil SKTM', prefix: 'sktm' }
};
let currentMode = 'ktp';

const el = (id) => document.getElementById(id);
const uploadZone = el('uploadZone');
const modeButtons = document.querySelectorAll('.mode-btn');
const modeIcon = el('modeIcon');
const uploadTitle = el('uploadTitle');
const uploadSubtitle = el('uploadSubtitle');
const fileInput = el('fileInput');
const cameraBox = el('cameraBox');
const cameraVideo = el('cameraVideo');
const cameraControls = el('cameraControls');
const guideFrame = el('guideFrame');
const guideText = el('guideText');
const closeCamera = el('closeCamera');
const captureButton = el('captureButton');
const pickGallery = el('pickGallery');
const captureCanvas = el('captureCanvas');
const previewBox = el('previewBox');
const previewImage = el('previewImage');
const previewInfo = el('previewInfo');
const cropButton = el('cropButton');
const retakeButton = el('retakeButton');
const manualButton = el('manualButton');
const resetButton = el('resetButton');
const statusBox = el('statusBox');
const manualCropBox = el('manualCropBox');
const manualTitle = el('manualTitle');
const manualStage = el('manualStage');
const manualImage = el('manualImage');
const manualMask = el('manualMask');
const applyManualButton = el('applyManualButton');
const cancelManualButton = el('cancelManualButton');

let selectedFile = null;
let selectedGuideCrop = null;
let selectedMode = currentMode;
let cameraStream = null;
let lastObjectUrl = null;
let manualRect = null;
let manualPointer = null;

modeButtons.forEach((button) => button.addEventListener('click', () => setMode(button.dataset.mode)));
uploadZone.addEventListener('click', openCamera);
pickGallery.addEventListener('click', () => fileInput.click());
closeCamera.addEventListener('click', stopCamera);
captureButton.addEventListener('click', captureFromCamera);
fileInput.addEventListener('change', (event) => {
  const file = event.target.files && event.target.files[0];
  if (file) {
    stopCamera();
    setSelectedFile(file, null, currentMode);
  }
});
cropButton.addEventListener('click', cropAndDownload);
retakeButton.addEventListener('click', retakePhoto);
manualButton.addEventListener('click', openManualCrop);
applyManualButton.addEventListener('click', applyManualCrop);
cancelManualButton.addEventListener('click', closeManualCrop);
resetButton.addEventListener('click', resetAll);
manualMask.addEventListener('pointerdown', startManualPointer);
window.addEventListener('pointermove', moveManualPointer);
window.addEventListener('pointerup', stopManualPointer);
window.addEventListener('resize', () => {
  if (manualCropBox.classList.contains('show')) initManualRect();
});
window.addEventListener('beforeunload', stopCamera);
document.addEventListener('visibilitychange', () => {
  if (document.hidden && cameraStream) stopCamera();
});

function getModeConfig(mode = currentMode) {
  return DOC_MODES[mode] || DOC_MODES.ktp;
}

function setMode(mode) {
  if (!DOC_MODES[mode]) return;
  currentMode = mode;
  selectedMode = mode;
  selectedFile = null;
  selectedGuideCrop = null;
  fileInput.value = '';
  previewBox.classList.remove('show');
  closeManualCrop();
  setReadyButtons(false);
  updateModeUi();
  setStatus('', '');
}

function updateModeUi() {
  const config = getModeConfig();
  modeButtons.forEach((button) => button.classList.toggle('active', button.dataset.mode === currentMode));
  modeIcon.textContent = config.icon;
  uploadTitle.textContent = `Ketuk untuk Kamera ${config.label}`;
  uploadSubtitle.textContent = `atau pilih foto ${config.label} dari galeri`;
  guideFrame.style.aspectRatio = `${config.ratio} / 1`;
  guideFrame.classList.toggle('a4', currentMode === 'sktm');
  guideText.textContent = currentMode === 'sktm'
    ? 'Yang masuk: seluruh dokumen A4 • Area gelap akan terpotong'
    : 'Yang masuk: seluruh KTP • Area gelap akan terpotong';
}

updateModeUi();

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
    closeManualCrop();
    setReadyButtons(false);
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
  const modeAtCapture = currentMode;
  const guideCrop = getGuideCropRect();
  captureCanvas.width = cameraVideo.videoWidth;
  captureCanvas.height = cameraVideo.videoHeight;
  captureCanvas.getContext('2d').drawImage(cameraVideo, 0, 0, captureCanvas.width, captureCanvas.height);
  stopCamera();
  captureCanvas.toBlob((blob) => {
    if (!blob) {
      setStatus('err', '❌ Gagal mengambil foto.');
      return;
    }
    const config = getModeConfig(modeAtCapture);
    const file = new File([blob], `${config.prefix}_capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
    setSelectedFile(file, guideCrop, modeAtCapture);
  }, 'image/jpeg', 0.95);
}

function getGuideCropRect() {
  const videoRect = cameraVideo.getBoundingClientRect();
  const frameRect = guideFrame.getBoundingClientRect();
  const videoW = cameraVideo.videoWidth;
  const videoH = cameraVideo.videoHeight;
  if (!videoRect.width || !videoRect.height || !videoW || !videoH) return null;

  const scale = Math.max(videoRect.width / videoW, videoRect.height / videoH);
  const renderedW = videoW * scale;
  const renderedH = videoH * scale;
  const offsetX = (videoRect.width - renderedW) / 2;
  const offsetY = (videoRect.height - renderedH) / 2;

  const leftOnElement = frameRect.left - videoRect.left;
  const topOnElement = frameRect.top - videoRect.top;
  const crop = {
    x: (leftOnElement - offsetX) / scale,
    y: (topOnElement - offsetY) / scale,
    w: frameRect.width / scale,
    h: frameRect.height / scale
  };
  crop.x = clamp(crop.x, 0, videoW - 1);
  crop.y = clamp(crop.y, 0, videoH - 1);
  crop.w = clamp(crop.w, 1, videoW - crop.x);
  crop.h = clamp(crop.h, 1, videoH - crop.y);
  return fitRectToRatio(crop, videoW, videoH, getModeConfig().ratio);
}

function setSelectedFile(file, guideCrop = null, mode = currentMode) {
  currentMode = mode;
  selectedMode = mode;
  updateModeUi();
  selectedFile = file;
  selectedGuideCrop = guideCrop;
  setReadyButtons(true);
  closeManualCrop();
  if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
  lastObjectUrl = URL.createObjectURL(file);
  previewImage.src = lastObjectUrl;
  previewInfo.textContent = `${file.name} • ${formatBytes(file.size)}`;
  previewBox.classList.add('show');
  const label = getModeConfig().label;
  setStatus('info', guideCrop ? `Siap disimpan. Crop ${label} akan mengikuti kotak putih saat foto tadi.` : `Siap dicrop sebagai ${label}. Kalau auto kurang pas, pakai Crop Manual.`);
}

function setReadyButtons(enabled) {
  cropButton.disabled = !enabled;
  retakeButton.disabled = !enabled;
  manualButton.disabled = !enabled;
}

function retakePhoto() {
  selectedFile = null;
  selectedGuideCrop = null;
  fileInput.value = '';
  previewBox.classList.remove('show');
  closeManualCrop();
  setReadyButtons(false);
  setStatus('', '');
  openCamera();
}

async function cropAndDownload() {
  if (!selectedFile) return;
  cropButton.disabled = true;
  cropButton.textContent = '⏳ Cropping...';
  setStatus('info', selectedGuideCrop ? '⏳ Memotong sesuai kotak guide...' : `⏳ Mencari tepi ${getModeConfig().label}...`);

  try {
    const blob = await autoCropDocument(selectedFile);
    if (!blob) {
      setStatus('err', '❌ Dokumen tidak terdeteksi. Pakai Crop Manual, atau foto ulang lebih terang.');
      return;
    }
    await downloadBlob(blob);
    clearSelectedAfterDownload();
  } catch (error) {
    console.error(error);
    setStatus('err', `❌ ${error.message || error}`);
  } finally {
    cropButton.disabled = !selectedFile;
    cropButton.textContent = '✂️ Crop & Download';
  }
}

async function autoCropDocument(file) {
  const image = await loadImage(file);
  if (selectedGuideCrop) {
    const blob = await cropImageToBlob(image, selectedGuideCrop, getModeConfig(selectedMode).ratio, selectedMode);
    URL.revokeObjectURL(image.src);
    return blob;
  }
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
  const targetRatio = getModeConfig(selectedMode).ratio;
  const currentRatio = cropW / cropH;
  if (Math.abs(currentRatio - targetRatio) > 0.05) {
    if (currentRatio > targetRatio) {
      const targetH = cropW / targetRatio;
      const delta = targetH - cropH;
      minY = Math.max(0, minY - delta / 2);
      maxY = Math.min(height, maxY + delta / 2);
    } else {
      const targetW = cropH * targetRatio;
      const delta = targetW - cropW;
      minX = Math.max(0, minX - delta / 2);
      maxX = Math.min(width, maxX + delta / 2);
    }
  }

  cropW = maxX - minX;
  cropH = maxY - minY;
  return cropImageToBlob(canvas, { x: minX, y: minY, w: cropW, h: cropH }, targetRatio, selectedMode);
}

function openManualCrop() {
  if (!selectedFile || !lastObjectUrl) return;
  selectedGuideCrop = null;
  manualTitle.textContent = `Crop Manual ${getModeConfig(selectedMode).label}`;
  manualImage.onload = () => requestAnimationFrame(initManualRect);
  manualImage.src = '';
  manualCropBox.classList.add('show');
  previewBox.classList.remove('show');
  setStatus('info', 'Geser kotak manual bebas lebar/tinggi ke area dokumen, lalu klik Pakai Crop Manual.');
  requestAnimationFrame(() => {
    manualImage.src = lastObjectUrl;
  });
}

function closeManualCrop() {
  manualCropBox.classList.remove('show');
  manualPointer = null;
  manualRect = null;
  if (selectedFile) previewBox.classList.add('show');
}

function initManualRect() {
  const bounds = getImageBoundsInStage();
  if (!bounds.width || !bounds.height) return;
  const ratio = getModeConfig(selectedMode).ratio;
  let w = bounds.width * (selectedMode === 'sktm' ? 0.62 : 0.82);
  let h = w / ratio;
  if (h > bounds.height * 0.86) {
    h = bounds.height * 0.86;
    w = h * ratio;
  }
  manualRect = {
    x: bounds.x + (bounds.width - w) / 2,
    y: bounds.y + (bounds.height - h) / 2,
    w,
    h
  };
  renderManualRect();
}

function startManualPointer(event) {
  if (!manualRect) return;
  event.preventDefault();
  manualMask.setPointerCapture?.(event.pointerId);
  const handle = event.target.dataset.handle || 'move';
  manualPointer = {
    id: event.pointerId,
    handle,
    startX: event.clientX,
    startY: event.clientY,
    rect: { ...manualRect }
  };
}

function moveManualPointer(event) {
  if (!manualPointer || event.pointerId !== manualPointer.id) return;
  event.preventDefault();
  const dx = event.clientX - manualPointer.startX;
  const dy = event.clientY - manualPointer.startY;
  const bounds = getImageBoundsInStage();
  let rect = { ...manualPointer.rect };

  if (manualPointer.handle === 'move') {
    rect.x += dx;
    rect.y += dy;
    rect = keepRectInside(rect, bounds);
  } else {
    rect = resizeManualRectFree(rect, manualPointer.handle, dx, dy, bounds);
  }

  manualRect = rect;
  renderManualRect();
}

function resizeManualRectFree(startRect, handle, dx, dy, bounds) {
  const minSize = Math.min(80, bounds.width * 0.18, bounds.height * 0.18);
  let left = startRect.x;
  let right = startRect.x + startRect.w;
  let top = startRect.y;
  let bottom = startRect.y + startRect.h;

  if (handle.includes('w')) left = clamp(startRect.x + dx, bounds.x, right - minSize);
  if (handle.includes('e')) right = clamp(startRect.x + startRect.w + dx, left + minSize, bounds.x + bounds.width);
  if (handle.includes('n')) top = clamp(startRect.y + dy, bounds.y, bottom - minSize);
  if (handle.includes('s')) bottom = clamp(startRect.y + startRect.h + dy, top + minSize, bounds.y + bounds.height);

  return {
    x: left,
    y: top,
    w: right - left,
    h: bottom - top
  };
}

function stopManualPointer(event) {
  if (manualPointer && event.pointerId === manualPointer.id) {
    manualPointer = null;
  }
}

function renderManualRect() {
  if (!manualRect) return;
  manualMask.style.left = `${manualRect.x}px`;
  manualMask.style.top = `${manualRect.y}px`;
  manualMask.style.width = `${manualRect.w}px`;
  manualMask.style.height = `${manualRect.h}px`;
  manualMask.style.setProperty('--crop-w', `${manualRect.w}px`);
  manualMask.style.setProperty('--crop-h', `${manualRect.h}px`);
}

async function applyManualCrop() {
  if (!selectedFile || !manualRect) return;
  applyManualButton.disabled = true;
  applyManualButton.textContent = '⏳ Menyimpan...';
  try {
    const image = await loadImage(selectedFile);
    const bounds = getImageBoundsInStage();
    const naturalW = image.naturalWidth || image.width;
    const naturalH = image.naturalHeight || image.height;
    const scaleX = naturalW / bounds.width;
    const scaleY = naturalH / bounds.height;
    const rect = {
      x: (manualRect.x - bounds.x) * scaleX,
      y: (manualRect.y - bounds.y) * scaleY,
      w: manualRect.w * scaleX,
      h: manualRect.h * scaleY
    };
    const safeRect = clampRectToImage(rect, naturalW, naturalH);
    const blob = await cropImageExactToBlob(image, safeRect);
    URL.revokeObjectURL(image.src);
    await downloadBlob(blob);
    closeManualCrop();
    clearSelectedAfterDownload();
  } catch (error) {
    console.error(error);
    setStatus('err', `❌ ${error.message || error}`);
  } finally {
    applyManualButton.disabled = false;
    applyManualButton.textContent = '✅ Pakai Crop Manual';
  }
}

function getImageBoundsInStage() {
  const stage = manualStage.getBoundingClientRect();
  const img = manualImage.getBoundingClientRect();
  return {
    x: img.left - stage.left,
    y: img.top - stage.top,
    width: img.width,
    height: img.height
  };
}

function keepRectInside(rect, bounds) {
  rect.w = Math.min(rect.w, bounds.width);
  rect.h = Math.min(rect.h, bounds.height);
  rect.x = clamp(rect.x, bounds.x, bounds.x + bounds.width - rect.w);
  rect.y = clamp(rect.y, bounds.y, bounds.y + bounds.height - rect.h);
  return rect;
}

async function downloadBlob(blob) {
  const dataUrl = await blobToDataUrl(blob);
  const config = getModeConfig(selectedMode);
  const filename = `${config.folder}/${buildFilename(config.prefix)}.jpg`;
  await chrome.downloads.download({ url: dataUrl, filename, saveAs: false });
  setStatus('ok', `✅ Berhasil disimpan: Downloads/${filename}`);
}

function clearSelectedAfterDownload() {
  selectedFile = null;
  selectedGuideCrop = null;
  fileInput.value = '';
  setReadyButtons(false);
  previewBox.classList.remove('show');
}

function cropImageToBlob(source, rect, ratio = getModeConfig(selectedMode).ratio, mode = selectedMode) {
  const config = getModeConfig(mode);
  const out = document.createElement('canvas');
  out.width = config.outputWidth;
  out.height = Math.round(config.outputWidth / ratio);
  out.getContext('2d').drawImage(source, rect.x, rect.y, rect.w, rect.h, 0, 0, out.width, out.height);
  return new Promise((resolve) => out.toBlob(resolve, 'image/jpeg', 0.92));
}

function cropImageExactToBlob(source, rect) {
  const out = document.createElement('canvas');
  out.width = Math.max(1, Math.round(rect.w));
  out.height = Math.max(1, Math.round(rect.h));
  out.getContext('2d').drawImage(source, rect.x, rect.y, rect.w, rect.h, 0, 0, out.width, out.height);
  return new Promise((resolve) => out.toBlob(resolve, 'image/jpeg', 0.92));
}

function clampRectToImage(rect, maxW, maxH) {
  let x = clamp(rect.x, 0, maxW - 1);
  let y = clamp(rect.y, 0, maxH - 1);
  let w = clamp(rect.w, 1, maxW - x);
  let h = clamp(rect.h, 1, maxH - y);
  return { x, y, w, h };
}

function fitRectToRatio(rect, maxW, maxH, targetRatio) {
  let { x, y, w, h } = rect;
  const ratio = w / h;
  if (Math.abs(ratio - targetRatio) > 0.01) {
    if (ratio > targetRatio) {
      const targetH = w / targetRatio;
      y -= (targetH - h) / 2;
      h = targetH;
    } else {
      const targetW = h * targetRatio;
      x -= (targetW - w) / 2;
      w = targetW;
    }
  }
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (x + w > maxW) x = Math.max(0, maxW - w);
  if (y + h > maxH) y = Math.max(0, maxH - h);
  w = Math.min(w, maxW - x);
  h = Math.min(h, maxH - y);
  return { x, y, w, h };
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
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

function buildFilename(prefix = getModeConfig(selectedMode).prefix) {
  const now = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${prefix}_${now.getFullYear()}${p(now.getMonth() + 1)}${p(now.getDate())}_${p(now.getHours())}${p(now.getMinutes())}${p(now.getSeconds())}`;
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
  selectedGuideCrop = null;
  fileInput.value = '';
  previewBox.classList.remove('show');
  closeManualCrop();
  setReadyButtons(false);
  cropButton.textContent = '✂️ Crop & Download';
  if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
  lastObjectUrl = null;
  setStatus('', '');
}
