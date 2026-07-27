# TGQ — Local to Online Deployment Guide

## Tujuan
Migrasi dashboard lokal TGQ menjadi website online yang dapat diakses melalui browser publik.

## Status Saat Ini
- **Server**: Berjalan di Termux native (192.168.1.5:8443)
- **UI**: Sudah menggunakan FluentUI icons + dark maroon gradient
- **Backend**: FastAPI + uvicorn
- **Akses**: Hanya lokal (LAN)

## Todo Prioritas

### 1. Persiapan Domain & SSL
- [ ] Daftarkan domain (misal: tgq-prediction.com)
- [ ] Setup Cloudflare DNS
- [ ] Generate SSL certificate (Let's Encrypt)

### 2. Port Forwarding / Tunnel
- [ ] Setup port forwarding di router (port 8443)
- [ ] Atau gunakan Cloudflare Tunnel untuk akses aman

### 3. Konfigurasi Server
- [ ] Update `api/main.py` untuk mendukung HTTPS
- [ ] Tambahkan CORS middleware
- [ ] Tambahkan rate limiting

### 4. Deployment
- [ ] Buat script deploy otomatis
- [ ] Setup auto-restart server
- [ ] Setup monitoring

### 5. Testing
- [ ] Test akses publik
- [ ] Test performa
- [ ] Test keamanan

## Catatan Teknis
- Target: Website online yang dapat diakses melalui browser
- Migrasi bertahap: LAN → Publik
- Dependency: Domain, SSL, port forwarding/tunnel

## Catatan Khusus
- Dokumen ini adalah persiapan, bukan implementasi final
- Perubahan kode akan dilakukan setelah dokumen ini dianggap cukup lengkap
