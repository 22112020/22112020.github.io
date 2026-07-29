# TGQ — Trust Generator Qualitynumber
### Native Termux Server — Samsung Galaxy Note 8

**Angka Bukan Lagi Tebakan.**  
TGQ adalah platform prediksi angka yang berjalan 24/7 dari **Samsung Galaxy Note 8** — murni **Native Termux**, tanpa emulasi atau container. Dibangun oleh **Mr.2211** untuk siapa saja yang mengutamakan akurasi, kecepatan, dan kemandirian infrastruktur.

---

## 📡 Arsitektur Server

### Hardware
| Komponen | Spesifikasi |
|---|---|
| **Device** | Samsung Galaxy Note 8 (SM-N950F) |
| **OS** | Android 9 — Native Termux |
| **CPU** | Exynos 8895 — 8 Core (4x M2 + 4x Cortex-A53) |
| **RAM** | 6 GB LPDDR4X |
| **Storage** | 64 GB UFS 2.1 |
| **Python** | 3.14 (Termux native) |
| **API Server** | Uvicorn + FastAPI (port 8443) |

### Software Stack
```
FastAPI (Python 3.14)
  ├── Uvicorn (ASGI server)
  ├── Pydantic (data validation)
  ├── CORSMiddleware (allow all origins)
  ├── core/executor.py (prediction orchestration)
  ├── core/market_sync.py (data_harian to pasaran_luna sync)
  ├── core/data_loader.py (read-only provider for engines)
  ├── core/hoki_generator.py (Hoki prediction)
  ├── engines/ (3 prediction engines)
  │   ├── toto_macau/
  │   ├── oregon/
  │   └── historical_trend/
  ├── config/ (market config, orphan mapping)
  ├── data_harian/ (raw input data)
  ├── pasaran_luna/ (processed market data)
  └── hoki_cache/ (cached predictions)
```

### Jaringan
- **Hostname**: `192.168.1.5`
- **Port API**: `8443`
- **SSH**: Port `8022`
- **Otentikasi**: SSH key (`~/.ssh/tgq_note8`)

---

## 🔗 Endpoint API

Semua endpoint tersedia dalam **dual mode** — dengan dan tanpa prefix `/api`.

### Status & Informasi
| Endpoint | Method | Deskripsi |
|---|---|---|
| `/` | GET | UI TGQ (SPA, 68KB) |
| `/status` | GET | Status server, uptime, engine & market count |
| `/api/status` | GET | Sama dengan `/status` |
| `/health` | GET | Health check sederhana |
| `/api/health` | GET | Sama dengan `/health` |
| `/engines` | GET | Daftar engine prediksi |
| `/api/engines` | GET | Sama dengan `/engines` |
| `/markets` | GET | Semua market (46 named + orphan) |
| `/api/markets` | GET | Sama dengan `/markets` |

### Prediksi
| Endpoint | Method | Deskripsi |
|---|---|---|
| `/totomacau` | GET | Prediksi Toto Macau (4D & 5D) |
| `/api/totomacau` | GET | Sama dengan `/totomacau` |
| `/oregon` | GET | Daftar pasar Oregon |
| `/api/oregon` | GET | Sama dengan `/oregon` |
| `/oregon/{market}` | GET | Prediksi Oregon spesifik |
| `/api/oregon/{market}` | GET | Sama dengan `/oregon/{market}` |
| `/predict` | POST | Prediksi via engine |
| `/api/predict` | POST | Sama dengan `/predict` |
| `/hoki` | GET | Angka Hoki hari ini |
| `/api/hoki` | GET | Sama dengan `/hoki` |

### Input Data
| Endpoint | Method | Deskripsi |
|---|---|---|
| `/input` | POST | Input data pasar |
| `/api/input` | POST | Sama dengan `/input` |
| `/trash` | POST | Simpan raw paste text |
| `/api/trash` | POST | Sama dengan `/trash` |
| `/trash/status` | GET | Status file trash |
| `/api/trash/status` | GET | Sama dengan `/trash/status` |
| `/sync` | POST | Sinkronisasi data_harian ke pasaran_luna |
| `/api/sync` | POST | Sama dengan `/sync` |

---

## 📊 Data Flow

```
Paste Text / API Input
        ↓
    data_harian/    -- Raw result files (*.md)
        ↓ sync
    pasaran_luna/   -- Processed market data (index.json)
        ↓ load
    data_loader     -- Read-only provider (engines only use this)
        ↓ predict
    engines/        -- toto_macau, oregon, historical_trend
        ↓ result
    Prediction      -- Confidence, main numbers, backup
```

---

## 🔐 Fitur Luna Paste

Fitur eksklusif untuk input data cepat, diproteksi password.

### Cara Pakai
1. **Paste** teks dari `data_harian` ke textarea
2. Klik **⚡ Parse** (tanpa password) atau **🔐 Luna Parse** (dengan password)
3. Luna Parse: Masukkan **password** `292511`
4. Sistem otomatis: Parse semua market (named + orphan) → Route ke input grid → Kirim ke `/api/input` → Tampilkan hasil ekstraksi

### Proteksi
- Password: **292511**
- Hanya yang authorized bisa input data massal

---

## 🐛 Bug Fix — TGQ Functions Not Exported (30 Juli 2026)

### Masalah
Fungsi `parsePaste()`, `lunaParse()`, `showLunaModal()`, `closeLunaModal()`, dan `renderLunaResults()` didefinisikan di dalam IIFE `const TGQ = (() => {...})()` tapi **tidak diekspor** di `return` statement. Akibatnya `TGQ.parsePaste = undefined`, `TGQ.showLunaModal = undefined` — tombol Parse dan Luna Parse tidak bereaksi saat diklik.

Error di console:
```
TypeError: TGQ.parsePaste is not a function
    at HTMLButtonElement.onclick (index.html:385:99)
```

### Root Cause
```javascript
// ❌ BEFORE — parsePaste dkk. tidak diekspor
return { init, predict, filterMarkets, startClock, showPage, addInputRow,
  removeInputRow, submitInput, clearInput, updateInputSummary };

// ✅ AFTER — semua fungsi Luna ditambahkan
return { init, predict, filterMarkets, startClock, showPage, addInputRow,
  removeInputRow, submitInput, clearInput, updateInputSummary,
  parsePaste, lunaParse, showLunaModal, closeLunaModal, renderLunaResults };
```

### Perbaikan
1. **`UI/index.html`** (lokal) — return statement fixed
2. **`index.html`** (GitHub Pages) — return statement fixed + full sync dari `UI/index.html`

### Verifikasi
| Tombol | Sebelum | Sesudah |
|--------|---------|--------|
| ⚡ Parse | ❌ Tidak bereaksi | ✅ Parse 32 market (named + orphan) |
| 🔐 Luna Parse | ❌ Tidak bereaksi | ✅ Modal password muncul, data terekstrak |
| onpaste auto-parse | ❌ Tidak bereaksi | ✅ Bekerja jika paste manual |

### Data Flow Parse
```
Paste text → textarea#lunaPaste
    ↓
TGQ.parsePaste() / TGQ.lunaParse()
    ↓
Sanitasi (buang UI artifacts: Play Now, btn_live, labelthumbnail, thumbnail, label)
    ↓
Split blocks by blank line
    ↓
TAHAP 1: Named markets (cari POOL → digit → PERIODE)
    ├── Normalisasi alias (TOTOMACAU → 4DTOTOMACAU, dll.)
    └── _fillInputRow(marketName, result, period)
    ↓
TAHAP 2: Orphan markets (position-based, 14 slot)
    ├── Pattern A: blank → DIGIT → blank
    ├── Pattern B: DIGIT → TIME (mm:ss) → btn_live
    └── Map via ORPHAN_SLOTS ke market name (HOKIDRAW, HUAHIN0100, dll.)
    ↓
updateInputSummary() + saveInputRows()
    ↓
Kirim ke /api/input (POST)
```

### File yang Diubah
| File | Lokasi | Perubahan |
|------|--------|-----------|
| `UI/index.html` | Lokal WSL | Return statement + Luna features |
| `index.html` | GitHub Pages | Full sync dari UI/index.html |
| `README.md` | Lokal | Dokumentasi bug fix |
| `local-readme.md` | Lokal (rahasia) | Update changelog

---

## 🧪 Testing

### Unit Tests
```bash
cd /data/data/com.termux/files/home/tgq
python3 -m unittest discover tests -v
```
**Status**: 98/98 tests OK

---

## 🔧 Maintenance

### Restart Server
```bash
pkill -f "uvicorn api.main"
cd /data/data/com.termux/files/home/tgq
nohup python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8443 > tgq_server.log 2>&1 &
```

### Update Code from GitHub
```bash
cd /data/data/com.termux/files/home/tgq
bash sync_from_github.sh
```

---

## 👑 Kredit

**TGQ — Trust Generator Qualitynumber**  
Dibangun oleh **Mr.2211** dari **Samsung Galaxy Note 8**.

> *"From Data to Digits — Precision You Can Trust."*

(c) 2026 Mr.2211 — TGQ Luna Core v1.0
