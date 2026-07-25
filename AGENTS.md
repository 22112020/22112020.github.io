# Luna Core — Agent Instructions

## Role

Senior Python Software Architect and Autonomous Coding Agent for **Togelku Luna Core**.

## Core Philosophy

DO NOT make the AI agent calculate directly.

**AI Agent:** understand request → call Luna Core → explain results
**Luna Core:** load data → load rules → execute analysis → generate reports

## Project Structure

```
Togelku/
├── core/
│   ├── executor.py         Engine execution coordinator
│   ├── market_sync.py      Sync data_harian → pasaran_luna (named + orphan)
│   ├── data_loader.py      Read-only data provider for engines
│   ├── result_finder.py    Result extraction from pasaran_luna/data_harian
│   ├── registry.py         Engine discovery via manifest
│   ├── rule_loader.py      Parse rules/*.md
│   ├── scanner.py          Project scanner
│   └── daily_generator.py  Create blank daily files
├── engines/
│   ├── base_engine.py      Abstract BaseEngine + PredictionResult
│   ├── oregon/             Oregon engine
│   └── toto_macau/         Toto Macau engine
├── config/
│   ├── luna_config.json
│   └── orphan_markets.json  14 orphan market slot positions
├── rules/
├── data_harian/            Source of truth (daily input files)
├── pasaran_luna/           Generated structured market histories
├── tests/                  90 tests
└── api/                    FastAPI server
```

## Current State — Complete Modules

- [x] Project scanner (`core/scanner.py`)
- [x] Engine registry (`core/registry.py`)
- [x] Manifest system (`engines/*/manifest.json`)
- [x] Rule loader (`core/rule_loader.py`)
- [x] Data loader (`core/data_loader.py`)
- [x] Result finder (`core/result_finder.py`)
- [x] Market sync (`core/market_sync.py`) — named + orphan markets
- [x] Executor (`core/executor.py`) — auto-sync before predict
- [x] Oregon engine (`engines/oregon/`)
- [x] Toto Macau engine (`engines/toto_macau/`)
- [x] Daily file generator (`core/daily_generator.py`)
- [x] API layer (`api/main.py`) — FastAPI, 8 endpoints
- [x] 90 tests across 10 test files

## Development Rules

1. Inspect entire repo before changing code.
2. Understand existing architecture.
3. Do not rewrite working components.
4. Preserve current folder structure.
5. Never remove modules without reason.
6. Never hardcode Windows paths.
7. Never put calculation logic inside AI prompts.
8. Every new module requires `module.py` + `test_module.py`.

## Data Contracts

### History Record Format
```
DD-MM-YYYY HH:MM:SS DAY PERIOD RESULT
```
Header: `History Nomor MARKET_NAME`
Append-only. Never edit old records.

### PredictionResult
```python
{
    "engine": str,
    "market": str,
    "target_period": str,
    "prediction": {"main": list[str], "backup": list[str]},
    "confidence": float,
    "metadata": {}
}
```

### index.json
```json
{"markets": {"NAME": {"name": "", "latest_period": "", "latest_result": "", "last_updated": ""}}, "last_sync": ""}
```

## Source Priority

1. **data_harian/** — source of truth, immutable
2. **pasaran_luna/** — generated from data_harian, fully rebuildable
3. **ResultFinder:** pasaran_luna → data_harian fallback
4. **DataLoader:** pasaran_luna → data_harian fallback
5. **Engines:** must use DataLoader only. Never read pasaran_luna or data_harian directly.

## Engine Hierarchy

```
BaseEngine (ABC)
 ├── OregonEngine    (engines/oregon/)
 └── TotoMacauEngine (engines/toto_macau/)
```

## Engine Manifest Contract

`engines/<name>/manifest.json`:
```json
{"name": "<name>", "module": "<module_path>", "class": "<ClassName>"}
```
Registry uses manifest as source of truth. Must NOT derive module/class names.

## Engine Rules

- Read-only. Never write history, market folders, data_harian, or index.json.
- Consume DataLoader output only. Never bypass DataLoader.
- Return structured PredictionResult.

## Auto Market Sync System

### Named Markets
Standard POOL-labeled markets are extracted by `_extract_market_entries()`.

### Orphan Markets (Banner Markets)
14 markets without POOL labels, extracted by **fixed position** relative to named POOL markets.

Mapping: `config/orphan_markets.json`

Positions (from current data_harian template):

```
After KING KONG 4D POOL:   orphan #0=HOKIdraw,      #1=huahin0100
After KENTUCKYEVE POOL:     orphan #0=cambodialotto
After BULLSEYE POOL:        orphan #0=poipet12
After OREGON12 POOL:        orphan #0=sydneylotto (thumbnail type)
After CHELSEA 15 POOL:      orphan #0=poipet15,     #1=totomali1530, #2=huahin1630
After CHELSEA 19 POOL:      orphan #0=poipet19
After PCSO POOL:            orphan #0=totomali2030, #1=huahin2100
After BRUNEI 21 POOL:       orphan #0=poipet22,     #1=hongkonglotto, #2=totomali2330
```

- Mapping is position-based, not value-based.
- `_extract_orphan_entries()` uses raw content (with UI markers) for position detection.
- Adding markets: append to `config/orphan_markets.json`. Never change existing slot order.

## Auto-Sync Before Predict

Every `Executor.execute()` call:
1. Validate inputs
2. Resolve market name alias
3. **Run MarketSync.sync_all()** — sync all data_harian files to pasaran_luna
4. Load market data via DataLoader
5. Run engine prediction

No cache checking. Always sync fresh. Required for multi-draw markets (Toto Macau).

## Market Name Aliases

Defined in `Executor.market_aliases`:
- "TOTO MACAU", "TOTO_MACAU", "TOTOMACAU" → "4DTOTOMACAU"

## Testing

```bash
.venv/bin/python -m unittest discover tests -v
```

Tests use `unittest`. Mock DataLoader/Registry where needed.
Temporary test files go inside project directory, not /tmp.

## Environment

- Python: 3.12+
- Timezone: Asia/Jakarta UTC+7
- Data format: Markdown (human-readable) + JSON (cache/index)
- Source date: extracted from filename `DD-MM-YYYY-Luna.md` only
- Never infer date from markdown content
- Yesterday's data can still be active — don't discard by date alone

## UI Artifacts to Filter

```python
{"labelthumbnail", "thumbnail", "Play Now", "btn_live"}
```
These are not market data. Must never become market names or result values.

## Version Contract

```yaml
LUNA_CORE_VERSION: 1.0
RULE_VERSION: 1
ENGINE_VERSION: 1
DATA_FORMAT_VERSION: 1
```

## Naming Convention

- market folder: lowercase, no spaces (e.g., `oregon03`)
- market display: UPPERCASE (e.g., `OREGON03`)
- engine file: `<name>_engine.py`
- engine name: lowercase (e.g., `oregon`)
- rule file: `<name>.md` or `<name>_v1.md`
