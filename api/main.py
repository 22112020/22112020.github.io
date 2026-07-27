import os
import json
import time
import re
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.executor import Executor
from core.market_sync import MarketSync

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIME_START_FILE = os.path.join(PROJECT_ROOT, '.run', 'server_start.txt')

def _get_server_start_time():
    os.makedirs(os.path.dirname(TIME_START_FILE), exist_ok=True)
    if os.path.exists(TIME_START_FILE):
        with open(TIME_START_FILE) as f:
            try:
                return float(f.read().strip())
            except (ValueError, OSError):
                pass
    now = time.time()
    with open(TIME_START_FILE, 'w') as f:
        f.write(str(now))
    return now

SERVER_START = _get_server_start_time()

def _format_uptime(elapsed: int) -> str:
    days = elapsed // 86400
    hours = (elapsed % 86400) // 3600
    minutes = (elapsed % 3600) // 60
    secs = elapsed % 60
    return f"{days:03d}-{hours:02d}-{minutes:02d}-{secs:02d}"

app = FastAPI(title='TGQ — Luna Core API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

ui_path = os.path.join(os.path.dirname(__file__), '..', 'UI', 'webapp')

MARKET_LIST = [
    '4DTOTOMACAU','5DTOTOMACAU','BANGKOK0130','BANGKOK0930','BRUNEI02','BRUNEI14','BRUNEI21',
    'BULLSEYE','CALIFORNIA','CAROLINADAY','CAROLINAEVE','CHELSEA11','CHELSEA15','CHELSEA19',
    'CHELSEA21','FLORIDAEVE','FLORIDAMID','JAKARTA1400','JAKARTA2330','KENTUCKYEVE','KENTUCKYMID',
    'KINGKONG4D','MAGNUM4D','NEVADA','NEWYORKEVE','NEWYORKMID','OREGON03','OREGON06','OREGON09',
    'OREGON12','PCSO','SINGAPORE',
    'HOKIDRAW','HUAHIN0100','CAMBODIALOTTO','POIPET12','SYDNEYLOTTO','POIPET15','TOTOMALI1530',
    'HUAHIN1630','POIPET19','TOTOMALI2030','HUAHIN2100','POIPET22','HONGKONGLOTTO','TOTOMALI2330',
]

MAX_PERIOD = 99999
MIN_PERIOD = 1
TRASH_REJECT_PATTERNS = ['labelthumbnail', 'btn_live', 'Play Now', 'thumbnail', 'label']
# --- Protection #2: Standardisasi naming folder ---
# Map raw extraction names (from trash input) -> standardized folder names.
# Prevents duplicate folders like: toto_macau_4d, toto_macau_5d, Togel, huahin_0100, etc.
MARKET_NAME_MAP = {
    "4D TOTO MACAU": "4dtotomacau",
    "5D TOTO MACAU": "5dtotomacau",
    "BANGKOK 0130": "bangkok0130",
    "BANGKOK 0930": "bangkok0930",
    "BRUNEI 02": "brunei02",
    "BRUNEI 14": "brunei14",
    "BRUNEI 21": "brunei21",
    "BULLSEYE": "bullseye",
    "CALIFORNIA": "california",
    "CAROLINA DAY": "carolinaday",
    "CAROLINA EVE": "carolinaeve",
    "CHELSEA 11": "chelsea11",
    "CHELSEA 15": "chelsea15",
    "CHELSEA 19": "chelsea19",
    "CHELSEA 21": "chelsea21",
    "FLORIDA EVE": "floridaeve",
    "FLORIDA MID": "floridamid",
    "JAKARTA 1400": "jakarta1400",
    "JAKARTA 2330": "jakarta2330",
    "KENTUCKY EVE": "kentuckyeve",
    "KENTUCKY MID": "kentuckymid",
    "KING KONG 4D": "kingkong4d",
    "MAGNUM 4D": "magnum4d",
    "NEVADA": "nevada",
    "NEW YORK EVE": "newyorkeve",
    "NEW YORK MID": "newyorkmid",
    "OREGON 03": "oregon03",
    "OREGON 06": "oregon06",
    "OREGON 09": "oregon09",
    "OREGON 12": "oregon12",
    "PCSO": "pcso",
    "SINGAPORE": "singapore",
    "HOKI DRAW": "hokidraw",
    "HUAHIN 0100": "huahin0100",
    "CAMBODIA LOTTO": "cambodialotto",
    "POIPET 12": "poipet12",
    "SYDNEY LOTTO": "sydneylotto",
    "POIPET 15": "poipet15",
    "TOTO MALI 1530": "totomali1530",
    "HUAHIN 1630": "huahin1630",
    "POIPET 19": "poipet19",
    "TOTO MALI 2030": "totomali2030",
    "HUAHIN 2100": "huahin2100",
    "POIPET 22": "poipet22",
    "HONG KONG LOTTO": "hongkonglotto",
    "TOTO MALI 2330": "totomali2330",
}


def _normalize_market_name(market_name: str) -> str:
    """Normalize market name to standard folder name.

    Uses MARKET_NAME_MAP for known markets, falls back to
    lowercase-no-spaces for unknown names.
    """
    up = market_name.strip().upper()
    if up in MARKET_NAME_MAP:
        return MARKET_NAME_MAP[up]
    fallback = re.sub(r'[^a-z0-9]', '', market_name.lower())
    _log_reject("unknown_market_name", f"input={market_name}, fallback={fallback}")
    return fallback


class PredictionRequest(BaseModel):
    engine: str
    market: str

class TrashRequest(BaseModel):
    content: str


def _log_reject(reason, detail=""):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[TRASH-REJECT] {ts} | {reason} | {detail}")


def _clean_trash_line(line):
    """Remove web UI artifacts from a trash line."""
    cleaned = line.strip()
    for pattern in TRASH_REJECT_PATTERNS:
        cleaned = cleaned.replace(pattern, '')
    return cleaned.strip()


@app.get('/status')
def status():
    try:
        executor = Executor()
        engines = executor.get_available_engines()
        last_sync = 'rebuilt on demand'
    except Exception:
        engines = []
        last_sync = 'unknown'
    uptime = _format_uptime(int(time.time() - SERVER_START))
    return {
        'app': 'TGQ',
        'version': '1.0',
        'status': 'ready',
        'uptime': uptime,
        'timezone': 'Asia/Jakarta',
        'engines': engines,
        'engine_count': len(engines),
        'markets': MARKET_LIST,
        'market_count': len(MARKET_LIST),
        'last_sync': last_sync,
    }

@app.get('/health')
def health():
    """Deep health check — tests engine, sync, and data integrity."""
    issues = []
    checks = {}

    # 1. Engine check
    try:
        executor = Executor()
        engines = executor.get_available_engines()
        checks['engines'] = {'status': 'ok', 'count': len(engines), 'list': engines}
        if not engines:
            issues.append('no engines available')
    except Exception as e:
        checks['engines'] = {'status': 'fail', 'error': str(e)}
        issues.append(f'engine discovery: {e}')

    # 2. Prediction test (Toto Macau)
    try:
        result = executor.execute('toto_macau', 'TOTO MACAU')
        d = result.to_dict()
        pred = d.get('prediction', {})
        main = pred.get('main', [])
        checks['prediction'] = {
            'status': 'ok',
            'engine': 'toto_macau',
            'target_period': d.get('target_period', ''),
            'main_count': len(main),
            'confidence': pred.get('confidence', 0),
        }
        if not main:
            issues.append('prediction returned empty main')
    except Exception as e:
        checks['prediction'] = {'status': 'fail', 'error': str(e)}
        issues.append(f'prediction: {e}')

    # 3. Sync dry-run
    try:
        sync = MarketSync()
        stats = sync.sync_all()
        checks['sync'] = {'status': 'ok', 'files_processed': stats['files_processed']}
    except Exception as e:
        checks['sync'] = {'status': 'fail', 'error': str(e)}
        issues.append(f'sync: {e}')

    # 4. Data directories
    for name, path in [('data_harian', 'data_harian'), ('pasaran_luna', 'pasaran_luna'), ('trash_dashboard', 'trash_dashboard')]:
        full = os.path.join(os.path.dirname(__file__), '..', path)
        exists = os.path.isdir(full)
        checks[name] = {'status': 'ok' if exists else 'missing'}
        if not exists:
            issues.append(f'{name} directory missing')

    # 5. Market count
    try:
        index_path = os.path.join(os.path.dirname(__file__), '..', 'pasaran_luna', 'index.json')
        if os.path.exists(index_path):
            with open(index_path) as f:
                idx = json.load(f)
            market_count = len(idx.get('markets', {}))
            checks['markets'] = {'status': 'ok', 'count': market_count}
        else:
            checks['markets'] = {'status': 'no_index'}
    except Exception as e:
        checks['markets'] = {'status': 'fail', 'error': str(e)}

    # 6. Disk usage
    try:
        import shutil
        total, used, free = shutil.disk_usage(os.path.dirname(__file__))
        checks['disk'] = {
            'total_gb': round(total / (1024**3), 1),
            'used_gb': round(used / (1024**3), 1),
            'free_gb': round(free / (1024**3), 1),
            'free_pct': round(free / total * 100, 1),
        }
        if free / total < 0.1:
            issues.append('disk space below 10%')
    except Exception:
        checks['disk'] = {'status': 'unavailable'}

    overall = 'healthy' if not issues else 'degraded'
    return {
        'status': overall,
        'uptime': _format_uptime(int(time.time() - SERVER_START)),
        'issues': issues if issues else None,
        'checks': checks,
    }


@app.get('/engines')
def engines():
    executor = Executor()
    available_engines = executor.get_available_engines()
    return {'engines': available_engines, 'count': len(available_engines)}

def _build_prediction_response(result, engine, market):
    d = result.to_dict()
    pred = d.get('prediction', {})
    meta = d.get('metadata', {})
    return {
        'success': True,
        'engine': engine,
        'market': market,
        'target_period': d.get('target_period', ''),
        'prediction': {
            'main': pred.get('main', []),
            'backup': pred.get('backup', []),
        },
        'confidence': pred.get('confidence', meta.get('confidence', 0)),
        'method': meta.get('method', pred.get('method', '')),
        'analysis': d.get('analysis', {}),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

@app.post('/analyze')
def analyze(request: PredictionRequest):
    executor = Executor()
    try:
        result = executor.execute(request.engine, request.market)
        return _build_prediction_response(result, request.engine, request.market)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Prediction failed: {str(e)}')

@app.get('/markets')
def markets():
    try:
        index_path = os.path.join(os.path.dirname(__file__), '..', 'pasaran_luna', 'index.json')
        if os.path.exists(index_path):
            with open(index_path, encoding='utf-8') as f:
                index_data = json.load(f)
            market_list = []
            seen = set()
            for name, info in index_data.get('markets', {}).items():
                if name in seen:
                    continue
                seen.add(name)
                market_list.append({
                    'name': name,
                    'latest_result': info.get('latest_result', ''),
                    'latest_period': info.get('latest_period', ''),
                    'last_updated': info.get('last_updated', ''),
                })
            return {'markets': market_list, 'count': len(market_list)}
        return {'markets': [], 'count': 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/sync')
def sync_markets():
    try:
        sync = MarketSync()
        stats = sync.sync_all()
        _rebuild_index_from_folders()
        return {'success': True, 'sync_stats': stats, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Sync failed: {str(e)}')

@app.get('/totomacau')
def toto_macau_prediction():
    executor = Executor()
    try:
        result = executor.execute('toto_macau', 'TOTO MACAU')
        return _build_prediction_response(result, 'toto_macau', 'TOTO MACAU')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Toto Macau prediction failed: {str(e)}')

@app.get('/oregon')
def oregon_options():
    return {
        'oregon_markets': ['OREGON03', 'OREGON06', 'OREGON09', 'OREGON12'],
        'usage': 'Use POST /analyze with {"engine": "oregon", "market": "OREGON03"}',
    }

@app.get('/oregon/{market}')
def oregon_prediction(market: str):
    valid_markets = ['OREGON03', 'OREGON06', 'OREGON09', 'OREGON12']
    if market not in valid_markets:
        raise HTTPException(status_code=400, detail=f'Invalid Oregon market. Must be one of: {valid_markets}')
    executor = Executor()
    try:
        result = executor.execute('oregon', market)
        return _build_prediction_response(result, 'oregon', market)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Oregon {market} prediction failed: {str(e)}')

def _extract_totomacau_from_text(text: str) -> list:
    """Extract Toto Macau entries (4D & 5D) from raw text.

    Returns list of dicts: {market, result, period}
    Rejects entries with period > MAX_PERIOD or < MIN_PERIOD.
    Cleans web UI artifacts from input.
    """
    entries = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cleaned = _clean_trash_line(line)
        s = cleaned.upper()
        if "TOTO MACAU" in s and "POOL" in s:
            market = "4D TOTO MACAU" if "4D" in s else "5D TOTO MACAU"
            result = ""
            period = ""
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = _clean_trash_line(lines[j])
                if next_line.isdigit() and len(next_line) in (4, 5):
                    result = next_line
                m = re.search(r'PERIODE\s*:\s*(\d+)', next_line, re.IGNORECASE)
                if m:
                    period = m.group(1)
            if market and result and period:
                p = int(period)
                if p >= MAX_PERIOD:
                    _log_reject("period_too_high", f"market={market}, period={period}, max={MAX_PERIOD}")
                    continue
                if p < MIN_PERIOD:
                    _log_reject("period_too_low", f"market={market}, period={period}, min={MIN_PERIOD}")
                    continue
                if not result.isdigit():
                    _log_reject("invalid_result", f"market={market}, result={result}")
                    continue
                entries.append({"market": _normalize_market_name(market), "result": result, "period": period})
    return entries


def _get_max_period_from_dataharian(data_dir: str, date: str = None) -> dict:
    """Scan ALL data_harian/*.md files for max 4D & 5D Toto Macau periods.

    Returns dict: {market_name: max_period_int}
    """
    result = {}
    for fname in os.listdir(data_dir):
        if fname.endswith(".md") and not fname.startswith("_"):
            fpath = os.path.join(data_dir, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    file_content = f.read()
                for entry in _extract_totomacau_from_text(file_content):
                    mkt = entry["market"]
                    p = int(entry["period"])
                    if mkt not in result or p > result[mkt]:
                        result[mkt] = p
            except Exception:
                pass
    return result


def _next_part_filename(data_dir: str, date: str) -> str:
    """Find next available -partX filename for given date."""
    part = 0
    while True:
        fname = f"{date}-Luna-part{part}.md"
        if not os.path.exists(os.path.join(data_dir, fname)):
            return fname
        part += 1


def _rebuild_index_from_folders():
    """Rebuild index.json from actual pasaran_luna folders. Deduplication guard."""
    base = os.path.join(os.path.dirname(__file__), '..', 'pasaran_luna')
    index_path = os.path.join(base, 'index.json')
    index = {"markets": {}}

    for item in sorted(os.listdir(base)):
        item_path = os.path.join(base, item)
        if not os.path.isdir(item_path) or item == '__pycache__':
            continue

        history_file = os.path.join(item_path, 'history.md')
        if not os.path.exists(history_file):
            continue

        latest_period = ''
        latest_result = ''
        total_records = 0

        try:
            with open(history_file, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('History') or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 5:
                        total_records += 1
                        latest_period = parts[3]
                        latest_result = parts[4]
        except Exception:
            continue

        market_key = item.upper()
        if market_key in index['markets']:
            existing = index['markets'][market_key]
            if total_records > existing.get('total_records', 0):
                index['markets'][market_key] = {
                    "name": market_key,
                    "latest_period": latest_period,
                    "latest_result": latest_result,
                    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "total_records": total_records,
                }
        else:
            index['markets'][market_key] = {
                "name": market_key,
                "latest_period": latest_period,
                "latest_result": latest_result,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_records": total_records,
            }

    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

    return len(index['markets'])


@app.post('/trash')
def save_trash(request: TrashRequest):
    trash_dir = os.path.join(os.path.dirname(__file__), '..', 'trash_dashboard')
    data_harian_dir = os.path.join(os.path.dirname(__file__), '..', 'data_harian')
    os.makedirs(trash_dir, exist_ok=True)
    os.makedirs(data_harian_dir, exist_ok=True)

    raw_lines = request.content.strip().splitlines()
    if len(raw_lines) > 400:
        raise HTTPException(status_code=400, detail=f'Max 400 lines, got {len(raw_lines)}')

    cleaned_lines = []
    for line in raw_lines:
        c = _clean_trash_line(line)
        if c:
            cleaned_lines.append(c)

    line_count = len(cleaned_lines)
    first_date = None
    for line in cleaned_lines:
        m = re.search(r'(\d{2}-\d{2}-\d{4})', line)
        if m:
            first_date = m.group(1)
            break
    if not first_date:
        first_date = datetime.now().strftime('%d-%m-%Y')

    filename = f'{first_date}-Trash.md'
    filepath = os.path.join(trash_dir, filename)

    existingTrashFiles = [f for f in os.listdir(trash_dir) if f.endswith('.md')]
    if existingTrashFiles:
        for f in existingTrashFiles:
            os.remove(os.path.join(trash_dir, f))

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines) + '\n')

    cleaned_content = '\n'.join(cleaned_lines)

    trash_entries = _extract_totomacau_from_text(cleaned_content)
    rejected_count = len(_extract_totomacau_from_text(request.content)) - len(trash_entries)
    new_entries = []
    if trash_entries:
        existing_max = _get_max_period_from_dataharian(data_harian_dir)
        for entry in trash_entries:
            mkt = entry["market"]
            p = int(entry["period"])
            if mkt not in existing_max or p > existing_max[mkt]:
                new_entries.append(entry)
            else:
                _log_reject("period_not_newer", f"market={mkt}, period={p}, existing_max={existing_max.get(mkt)}")

    if new_entries:
        part_name = _next_part_filename(data_harian_dir, first_date)
        part_path = os.path.join(data_harian_dir, part_name)
        lines_out = []
        for entry in new_entries:
            lines_out.append(f"{entry['market']} POOL")
            lines_out.append(entry["result"])
            lines_out.append(f"[PERIODE : {entry['period']}]")
            lines_out.append("")
        with open(part_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines_out) + "\n")
        harvested = {"file": part_name, "entries": len(new_entries)}
    else:
        harvested = None

    try:
        sync = MarketSync()
        stats = sync.sync_all()
        _rebuild_index_from_folders()
    except Exception as e:
        stats = {'error': str(e)}

    return {
        'success': True,
        'file': filename,
        'lines': line_count,
        'date': first_date,
        'sync_stats': stats,
        'harvested': harvested,
        'rejected': rejected_count if rejected_count > 0 else None,
    }

@app.get('/trash/status')
def trash_status():
    trash_dir = os.path.join(os.path.dirname(__file__), '..', 'trash_dashboard')
    os.makedirs(trash_dir, exist_ok=True)
    files = []
    total_lines = 0
    if os.path.isdir(trash_dir):
        for f in sorted(os.listdir(trash_dir)):
            if f.endswith('.md'):
                fp = os.path.join(trash_dir, f)
                with open(fp, encoding='utf-8') as fh:
                    content = fh.read()
                    lines = len(content.strip().splitlines())
                    total_lines += lines
                files.append({'name': f, 'lines': lines, 'size': os.path.getsize(fp)})
    return {'files': files, 'count': len(files), 'total_lines': total_lines}

if os.path.isdir(ui_path):
    with open(os.path.join(ui_path, 'index.html'), encoding='utf-8') as f:
        _index_html = f.read()

    @app.get('/ui/{rest_of_path:path}')
    def ui_files(rest_of_path: str):
        path = os.path.join(ui_path, rest_of_path or '')
        if os.path.isfile(path):
            return FileResponse(path)
        return HTMLResponse(_index_html)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
