# KTP / SKTM Auto-Crop Chrome Extension

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
6. Pin extension **KTP / SKTM Auto-Crop** kalau mau gampang dibuka.

## Cara Pakai

1. Klik icon extension → **Buka Kamera**.
2. Pilih mode:
   - **Foto KTP** untuk KTP.
   - **Foto SKTM (A4)** untuk dokumen A4.
3. Foto dokumen atau pilih dari galeri.
4. Pastikan seluruh dokumen masuk area kotak putih.
5. Kalau posisi kurang pas, klik **Foto Ulang**.
6. Klik **Crop & Download** untuk crop otomatis/guide.
7. Kalau hasil crop kurang pas, klik **Crop Manual**:
   - Geser kotak crop ke dokumen.
   - Tarik sudut kotak untuk memperbesar/perkecil bebas lebar/tinggi.
   - Klik **Pakai Crop Manual**.
8. Hasil masuk ke folder sesuai mode:
   ```
   Downloads/Hasil KTP/
   Downloads/Hasil SKTM/
   ```

## Catatan

- Extension berjalan offline/lokal.
- Tidak perlu server, port 8080, atau jaringan HP-PC.
- Kamera butuh izin dari Chrome/Edge saat pertama dipakai.
- Untuk foto dari kamera, crop otomatis mengikuti kotak putih di layar, jadi lebih stabil daripada deteksi tepi otomatis.
- Crop manual tersedia untuk KTP dan SKTM, bebas rasio sesuai kotak yang ditarik operator.
- Mode KTP/SKTM menentukan folder output dan default kotak awal.
- Kalau kamera kantor tidak ada, tetap bisa pilih file gambar dari galeri.
