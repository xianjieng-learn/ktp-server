# KTP Upload Server (Zero Dependencies)

Buka URL di HP → Foto KTP → Auto-Crop di Browser → Tersimpan di Komputer!

**Tidak perlu install apapun!** Cukup Python bawaan Windows.

## Requirements

- Python 3.6+ (sudah ada di semua Windows/Mac)
- Tidak perlu pip install!

## Jalankan

```bash
python server.py
```

Server akan menampilkan URL untuk diakses dari HP.

## Cara Pakai

1. **Pastikan HP & komputer di WiFi yang sama**
2. **Buka browser di HP** → ketik URL yang tertera
3. **Foto/Upload KTP** → ketuk area upload
4. **KTP otomatis ter-crop di browser HP** ✅
5. **Hasilnya tersimpan di komputer!**

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│  SEBELUM (Lambat):                                       │
│  HP → WhatsApp → WhatsApp Web → Download → Upload        │
│  ⏱️ ~2-3 menit per KTP                                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  SESUDAH (Cepat!):                                       │
│  HP → Buka URL → Foto → Auto-Crop → Tersimpan ✅        │
│  ⏱️ ~10 detik per KTP                                    │
└─────────────────────────────────────────────────────────┘
```

## Fitur

- 📱 **Mobile-friendly** — UI dirancang untuk HP
- 📷 **Camera capture** — langsung ambil foto dari browser
- ✂️ **Auto-crop** — detect & crop KTP di browser HP
- ✨ **Enhance** — perbaiki kualitas gambar
- 📋 **History** — lihat upload terakhir
- 🐍 **Zero dependencies** — cukup Python bawaan!

## Port Custom

```bash
python server.py --port 3000
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
