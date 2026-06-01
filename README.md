# KTP Upload Server

Buka URL di HP → Foto KTP → Auto-Crop → Tersimpan di komputer!

## Setup

```bash
pip install flask opencv-python numpy
```

## Jalankan

```bash
python server.py
```

Server akan menampilkan URL untuk diakses dari HP.

## Cara Pakai

1. **Pastikan HP & komputer di WiFi yang sama**
2. **Buka browser di HP** → ketik URL yang tertera
3. **Foto/Upload KTP** → ketuk area upload
4. **KTP otomatis ter-crop** dan tersimpan di komputer!

## Output

Foto KTP yang sudah di-crop tersimpan di folder `ktp_photos/` dengan nama:
```
ktp_20260601_153022.jpg
```

## Fitur

- 📱 **Mobile-friendly** — UI dirancang untuk HP
- 📷 **Camera capture** — langsung ambil foto dari browser
- 🖼️ **Drag & drop** — atau upload dari gallery
- ✂️ **Auto-crop** — detect & straighten KTP otomatis
- ✨ **Enhance** — perbaiki kualitas gambar
- 📋 **History** — lihat upload terakhir

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│  SEBELUM:                                                │
│  HP → WhatsApp → WhatsApp Web → Download → Crop Manual   │
│  ⏱️ ~2-3 menit per KTP                                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  SESUDAH:                                                │
│  HP → Buka URL → Foto → Auto-Crop ✅                     │
│  ⏱️ ~15 detik per KTP                                    │
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### HP gak bisa akses server
- Pastikan HP & komputer di WiFi yang sama
- Coba matikan firewall sementara
- Pastikan Python tidak diblokir

### KTP tidak terdeteksi
- Foto dari angle yang lebih frontal
- Pastikan KTP terlihat jelas
- Lighting cukup

## Port Custom

```bash
python server.py --port 3000
```

## Auto-Open Browser

```bash
python server.py --open
```
