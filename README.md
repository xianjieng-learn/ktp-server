# KTP Upload Server

Foto KTP di HP → Auto-Crop → Download di Komputer

## Jalankan

```bash
python server.py
```

## Cara Pakai

### 1. Buka di HP
```
http://192.168.x.x:8080/hp
```
- Foto KTP → Auto-Crop → Upload

### 2. Buka di Komputer
```
http://localhost:8080/pc
```
- Lihat semua foto KTP
- Klik **Download** untuk simpan

## Flow

```
📱 HP: /hp → Foto → Auto-Crop → Upload
                ↓
💻 PC: /pc → Lihat → Download ✅
```

## Fitur

- 📱 **HP**: Camera capture + auto-crop
- 💻 **PC**: Gallery + download
- 🐍 **Zero install**: Cukup Python bawaan
- 🧩 **Chrome Extension**: bisa pakai tanpa server/Python, hasil KTP dan SKTM langsung ke Downloads

## Versi Chrome Extension

Kalau tidak mau jalanin server Python:

1. Buka `chrome://extensions/`
2. Aktifkan **Developer mode**
3. Klik **Load unpacked**
4. Pilih folder `extension/`
5. Klik icon **KTP Auto-Crop** → **Buka Kamera**
6. Pilih mode **Foto KTP** atau **Foto SKTM (A4)**
7. Masukkan dokumen ke kotak putih, klik foto, lalu pakai **Foto Ulang** kalau posisinya belum pas
8. Klik **Crop & Download**
9. Kalau hasil crop kurang pas, klik **Crop Manual**, geser/resize kotak bebas, lalu klik **Pakai Crop Manual**. Hasil manual crop mengikuti kotak asli, tidak dipanjangin ke rasio KTP/A4.

Hasil crop masuk folder sesuai mode:
- KTP: `Downloads/Hasil KTP/`
- SKTM: `Downloads/Hasil SKTM/`
