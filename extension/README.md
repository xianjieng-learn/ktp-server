# KTP Auto-Crop Chrome Extension

Versi extension dari KTP server. Tidak perlu menjalankan `python server.py`.

## Install di Chrome / Edge

1. Download/clone repo ini.
2. Buka Chrome: `chrome://extensions/`
3. Aktifkan **Developer mode**.
4. Klik **Load unpacked**.
5. Pilih folder:
   ```
   ktp-server/extension
   ```
6. Pin extension **KTP Auto-Crop** kalau mau gampang dibuka.

## Cara Pakai

1. Klik icon extension → **Buka Kamera**.
2. Foto KTP atau pilih dari galeri.
3. Pastikan seluruh KTP masuk area kotak putih.
4. Kalau posisi kurang pas, klik **Foto Ulang**.
5. Klik **Crop & Download**.
6. Hasil masuk ke:
   ```
   Downloads/Hasil KTP/
   ```

## Catatan

- Extension berjalan offline/lokal.
- Tidak perlu server, port 8080, atau jaringan HP-PC.
- Kamera butuh izin dari Chrome/Edge saat pertama dipakai.
- Untuk foto dari kamera, crop mengikuti kotak putih di layar, jadi lebih stabil daripada deteksi tepi otomatis.
- Kalau kamera kantor tidak ada, tetap bisa pilih file gambar dari galeri.
