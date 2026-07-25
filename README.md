# TGQ — Trust Generator Qualitynumbers

**Modular local analysis engine for lottery prediction.**

- **Path:** `/mnt/d/Alfian/Togelku/`
- **Python:** 3.12+ — `.venv/bin/python`
- **Timezone:** Asia/Jakarta (UTC+7)
- **Tests:** 90 — `.venv/bin/python -m unittest discover tests -v`

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│  User / API / Leafia                              │
│         │                                         │
│         ▼                                         │
│  ┌──────────────┐                                 │
│  │  Executor     │  core/executor.py               │
│  │  auto-sync →  │  selalu sync data_harian dulu   │
│  │  resolve      │  alias market → load data →     │
│  │  predict      │  engine → return result         │
│  └──────┬───────┘                                 │
│         │                                         │
│    ┌────┴────────────────────┐                    │
│    ▼                         ▼                    │
│  MarketSync               Registry                │
│  core/market_sync.py       core/registry.py       │
│  data_harian → pasaran_luna engine discovery      │
│  named + orphan markets    via manifest.json      │
│    │                         │                    │
│    ▼                         ▼                    │
│  pasaran_luna/            Engines                 │
│  structured histories     oregon / toto_macau     │
│  + index.json                │                    │
│    │                         │                    │
│    └─────────┬───────────────┘                    │
│              ▼                                    │
│         DataLoader                                │
│         core/data_loader.py                       │
│         read-only provider                       │
│              │                                    │
│              ▼                                    │
│         ResultFinder                              │
│         core/result_finder.py                     │
│         pasaran_luna → data_harian fallback      │
└──────────────────────────────────────────────────┘
```

**Data flow:**

```
data_harian/*.md  (source of truth, immutable)
       │
       ▼  MarketSync.sync_all() — append-only
pasaran_luna/<market>/history.md  (fully rebuildable)
       │
       ▼  DataLoader.load_market() — read-only
   Prediction Engine
```

---

## Market Coverage — 47 Markets

### Named POOL Markets (33)
Standard markets with `POOL` label — auto-detected.

4D TOTO MACAU | 5D TOTO MACAU | BANGKOK 0130 | BANGKOK 0930
BRUNEI 02 | BRUNEI 14 | BRUNEI 21 | BULLSEYE
CALIFORNIA | CAROLINADAY | CAROLINAEVE | CHELSEA 11
CHELSEA 15 | CHELSEA 19 | CHELSEA 21 | FLORIDAEVE
FLORIDAMID | JAKARTA 1400 | JAKARTA 2330 | KENTUCKYEVE
KENTUCKYMID | KING KONG 4D | MAGNUM4D | NEVADA
NEWYORKEVE | NEWYORKMID | OREGON03 | OREGON06
OREGON09 | OREGON12 | PCSO | SINGAPORE

### Orphan Banner Markets (14)
Markets tanpa label `POOL`, diekstrak berdasarkan **posisi tetap**.
Mapping di `config/orphan_markets.json`.

HOKIdraw | huahin0100 | cambodialotto | poipet12
sydneylotto | poipet15 | totomali1530 | huahin1630
poipet19 | totomali2030 | huahin2100 | poipet22
hongkonglotto | totomali2330

---

## Project Structure

```
/mnt/d/Alfian/Togelku/
├── core/                 8 modules
│   ├── executor.py       Coordinator + auto-sync
│   ├── market_sync.py    data_harian → pasaran_luna
│   ├── data_loader.py    Read-only provider
│   ├── result_finder.py  Result extraction
│   ├── registry.py       Engine discovery
│   ├── rule_loader.py    rules/*.md parser
│   ├── scanner.py        Project scanner
│   └── daily_generator.py
├── engines/
│   ├── base_engine.py    Abstract + PredictionResult
│   ├── oregon/           Oregon 03/06/09/12
│   └── toto_macau/       Toto Macau
├── config/
│   ├── luna_config.json
│   └── orphan_markets.json
├── rules/                Algorithm rules (markdown)
├── data_harian/          Daily input files
├── pasaran_luna/         50 market histories + index
├── UI/                   GUI/UX prototypes
│   ├── webapp/           Web dashboard
│   └── android/          Android design concept
├── tests/                90 tests
├── api/
│   └── main.py           FastAPI — 8 endpoints
├── AGENTS.md             Agent instructions
├── leafia.md             Leafia usage guide
├── README.md             This file
└── .gitignore
```

---

## Quick Start

```python
from core.executor import Executor

ex = Executor()

# Toto Macau (auto-sync, latest data)
r = ex.execute("toto_macau", "TOTO MACAU")
print(r.to_dict())
# → target_period: 13771, main: [0,3,9,1,4], backup: [8]

# Oregon
r = ex.execute("oregon", "OREGON03")
print(r.to_dict())
```

### API Server

```bash
.venv/bin/python api/main.py

curl http://localhost:8000/status
curl http://localhost:8000/totomacau
curl http://localhost:8000/oregon/OREGON03
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"engine":"toto_macau","market":"TOTO MACAU"}'
```

---

## Engines

| Engine | Markets | Method |
|--------|---------|--------|
| **Toto Macau** | 4DTOTOMACAU | Similarity ×2 + frequency, 5 source markets |
| **Oregon** | OREGON03/06/09/12 | Digit frequency, 3 sources, history elimination |

---

## Key Rules

- **Auto-sync before predict:** setiap `execute()` langsung sync `data_harian/`
- **Engines read-only:** cuma pakai DataLoader, ga boleh bypass
- **data_harian** = source of truth, **pasaran_luna** = fully rebuildable
- **Orphan extraction:** position-based, bukan value-based
- **Source date:** dari filename `DD-MM-YYYY-Luna.md`, bukan dari konten

---

## Testing

```bash
.venv/bin/python -m unittest discover tests -v
```

90 tests, 10 files, semua core module + engines + edge cases.

---

## Tech

Python 3.12+ | FastAPI | unittest | Markdown data | JSON cache
