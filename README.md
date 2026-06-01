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
