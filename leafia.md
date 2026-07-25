# Leafia — TGQ Usage Guide

## Who is Leafia?

Leafia adalah AI agent (OpenClaws) yang terinstall di lingkungan `/mnt/d/Alfian/`.
TGQ (`/mnt/d/Alfian/Togelku/`) adalah bagian dari ekosistem Leafia dan bisa diakses penuh.

## Batasan — JANGAN DIANGGAP REMEH

Leafia **DILARANG KERAS** mengubah apapun di proyek TGQ:

| Dilarang | Contoh |
|----------|--------|
| Modify file module | `core/*.py`, `engines/*.py`, `api/*.py` |
| Edit konfigurasi | `config/*.json` (kecuali diminta user) |
| Hapus/rename file proyek | Folder `core/`, `engines/`, `tests/`, dll. |
| Tambah module baru | Tanpa persetujuan user |
| Tulis ulang history | `pasaran_luna/*/history.md` |
| Ubah data_harian | `data_harian/*.md` (source of truth) |

**Yang DIPERBOLEHKAN:**

| Diperbolehkan | Contoh |
|---------------|--------|
| Baca file proyek | Untuk memahami struktur, kode, data |
| Jalankan prediksi | `from core.executor import Executor` |
| Baca data | `data_harian/`, `pasaran_luna/`, `rules/` |
| Dokumentasi | `README.md`, `AGENTS.md` (jika diminta) |
| File baru di root | Hanya jika diminta user secara eksplisit |

## Cara Menggunakan TGQ

### 1. Prediksi Toto Macau

```python
from core.executor import Executor

executor = Executor()
result = executor.execute("toto_macau", "TOTO MACAU")
print(result.to_dict())
```

Setiap request prediksi akan otomatis:
- Sync data terbaru dari `data_harian/` ke `pasaran_luna/`
- Load market data
- Jalankan engine prediction
- Return PredictionResult

### 2. Prediksi Oregon

```python
from core.executor import Executor

executor = Executor()

for market in ["OREGON03", "OREGON06", "OREGON09", "OREGON12"]:
    result = executor.execute("oregon", market)
    print(f"{market}: {result.prediction}")
```

### 3. Cek Available Engines

```python
from core.executor import Executor

executor = Executor()
print(executor.get_available_engines())
# → ['oregon', 'toto_macau']
```

### 4. Multiple Predictions

```python
from core.executor import Executor

executor = Executor()
requests = [("toto_macau", "TOTO MACAU"), ("oregon", "OREGON03")]
results = executor.execute_multiple(requests)

for r in results:
    print(r.to_dict())
```

### 5. Via API

```bash
curl http://localhost:8000/totomacau
curl http://localhost:8000/oregon/OREGON03
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"engine": "toto_macau", "market": "TOTO MACAU"}'
```

## Struktur Penting

| Path | Fungsi |
|------|--------|
| `data_harian/` | Daily input files — source of truth |
| `pasaran_luna/` | Generated histories — jangan diedit langsung |
| `config/orphan_markets.json` | Mapping 14 orphan market slot — jangan diubah |
| `rules/` | Algorithm rules untuk engine |
| `core/executor.py` | Entry point prediksi — jangan dimodifikasi |
| `tests/` | 90 test — untuk verifikasi |

## Catatan Penting

- Selalu panggil `Executor()` langsung — **jangan** bypass DataLoader
- Jangan akses `data_harian/` atau `pasaran_luna/` langsung untuk prediksi
- Kalau ragu, tanya user sebelum bertindak
- File TGQ tidak boleh diedit tanpa persetujuan eksplisit user
