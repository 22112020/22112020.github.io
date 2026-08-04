from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.executor import Executor
from core.market_sync import MarketSync
from core.hoki_generator import HokiGenerator
from datetime import datetime
import os
import json

app = FastAPI(title='TGQ — Luna Core API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

MARKET_LIST = [
    '4DTOTOMACAU','5DTOTOMACAU','BANGKOK0130','BANGKOK0930','BRUNEI02','BRUNEI14','BRUNEI21',
    'BULLSEYE','CALIFORNIA','CAROLINADAY','CAROLINAEVE','CHELSEA11','CHELSEA15','CHELSEA19',
    'CHELSEA21','FLORIDAEVE','FLORIDAMID','JAKARTA1400','JAKARTA2330','KENTUCKYEVE','KENTUCKYMID',
    'KINGKONG4D','MAGNUM4D','NEVADA','NEWYORKEVE','NEWYORKMID','OREGON03','OREGON06','OREGON09',
    'OREGON12','PCSO','SINGAPORE',
    'HOKIDRAW','HUAHIN0100','CAMBODIALOTTO','POIPET12','SYDNEYLOTTO','POIPET15','TOTOMALI1530',
    'HUAHIN1630','POIPET19','TOTOMALI2030','HUAHIN2100','POIPET22','HONGKONGLOTTO','TOTOMALI2330',
    'HONGKONG_POOLS','SYDNEY_POOLS','SINGAPORE_POOLS',
]

class PredictionRequest(BaseModel):
    engine: str
    market: str

LANDING_HTML = r"""
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TGQ — Prediksi Togel Cerdas</title>
<style>
/* ===== CSS Variables — Future-Proof Theming ===== */
:root {
  --bg-primary: #0a0510;
  --bg-card: rgba(255,255,255,.04);
  --bg-card-hover: rgba(255,255,255,.08);
  --border-card: rgba(255,255,255,.06);
  --border-card-hover: rgba(192,57,43,.3);
  --text-primary: #f0e6f0;
  --text-secondary: #999;
  --text-muted: #666;
  --accent-1: #c0392b;
  --accent-2: #8e44ad;
  --accent-3: #c084fc;
  --accent-glow: rgba(192,57,43,.3);
  --gradient-hero: linear-gradient(135deg,#fff 30%,#c084fc 70%,#f59e0b);
  --gradient-btn: linear-gradient(135deg,#c0392b,#8e44ad);
  --gradient-ball: linear-gradient(135deg,#c0392b,#e74c3c);
  --gradient-ball-bu: linear-gradient(135deg,#7c3aed,#a78bfa);
  --font: 'Inter',sans-serif;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --shadow-card: 0 12px 40px rgba(0,0,0,.3);
  --transition: all .25s ease;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font);background:var(--bg-primary);color:var(--text-primary);min-height:100vh;overflow-x:hidden}

/* ===== Fluent Icons ===== */
.ficon{display:inline-block;vertical-align:-0.25em;flex-shrink:0}
.figlyph{display:inline-flex;align-items:center;justify-content:center;vertical-align:middle}
button{display:inline-flex;align-items:center;justify-content:center;gap:6px}
.figlyph.lg{width:48px;height:48px;border-radius:14px;background:rgba(192,57,43,.12);border:1px solid rgba(192,57,43,.2);margin-bottom:12px;color:var(--accent-3)}
.figlyph.iconbox{width:32px;height:32px;background:var(--gradient-btn);border-radius:var(--radius-sm);color:#fff;box-shadow:0 4px 12px var(--accent-glow)}
.figlyph.fcolor{color:var(--accent-3)}

/* ===== Background Orbs ===== */
.bg-orb{position:fixed;border-radius:50%;filter:blur(120px);pointer-events:none;z-index:0}
.orb1{width:600px;height:600px;background:radial-gradient(circle,rgba(180,50,80,.25),transparent);top:-200px;left:-200px}
.orb2{width:500px;height:500px;background:radial-gradient(circle,rgba(120,40,160,.2),transparent);bottom:-150px;right:-150px}
.orb3{width:400px;height:400px;background:radial-gradient(circle,rgba(200,150,50,.12),transparent);top:40%;left:50%}

/* ===== Layout ===== */
.content{position:relative;z-index:1;max-width:1200px;margin:0 auto;padding:20px}
.section{padding:40px 0}

/* ===== Navigation ===== */
nav{display:flex;align-items:center;justify-content:space-between;padding:16px 0;border-bottom:1px solid var(--border-card);margin-bottom:20px;position:sticky;top:0;background:rgba(10,5,16,.85);backdrop-filter:blur(16px);z-index:100}
.logo{display:flex;align-items:center;gap:12px}
.logo-icon{width:42px;height:42px;background:var(--gradient-btn);border-radius:var(--radius-md);display:flex;align-items:center;justify-content:center;font-weight:900;font-size:20px;color:#fff;box-shadow:0 4px 20px var(--accent-glow)}
.logo-text{font-size:22px;font-weight:800;background:var(--gradient-hero);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.logo-sub{font-size:11px;color:var(--text-muted);letter-spacing:2px;text-transform:uppercase;margin-top:-2px}
.nav-links{display:flex;gap:8px;align-items:center}
.nav-links a{color:var(--text-secondary);text-decoration:none;font-size:13px;font-weight:500;padding:8px 16px;border-radius:var(--radius-sm);transition:var(--transition);display:inline-flex;align-items:center;gap:6px}
.nav-links a .ficon{color:var(--accent-3);opacity:.7}
.nav-links a.active .ficon,.nav-links a:hover .ficon{opacity:1}
.nav-links a:hover,.nav-links a.active{color:var(--text-primary);background:var(--bg-card)}
.nav-status{display:flex;align-items:center;gap:6px;background:var(--bg-card);padding:6px 14px;border-radius:20px;font-size:12px;color:#8f8;margin-left:8px}
.nav-status .dot{width:7px;height:7px;background:#4f4;border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* ===== Hero ===== */
.hero{text-align:center;padding:50px 20px 30px}
.hero-badge{display:inline-block;background:rgba(192,57,43,.15);border:1px solid rgba(192,57,43,.25);color:#e74c3c;padding:6px 18px;border-radius:20px;font-size:12px;font-weight:600;letter-spacing:1px;margin-bottom:20px}
.hero h1{font-size:clamp(32px,5vw,56px);font-weight:900;line-height:1.1;margin-bottom:12px;background:var(--gradient-hero);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:clamp(14px,1.8vw,18px);color:var(--text-secondary);max-width:600px;margin:0 auto 24px;line-height:1.6}
.hero-actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}

/* ===== Digital Clock ===== */
.clock-section{text-align:center;padding:20px 0 40px}
.clock-time{font-size:clamp(48px,8vw,96px);font-weight:900;font-variant-numeric:tabular-nums;background:var(--gradient-hero);-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1;letter-spacing:4px;font-family:monospace}
.clock-date{font-size:clamp(16px,2vw,22px);color:var(--text-secondary);margin-top:8px;font-weight:500}
.clock-tz{font-size:12px;color:var(--text-muted);margin-top:4px;letter-spacing:1px}

/* ===== Buttons ===== */
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 28px;border-radius:var(--radius-md);font-size:15px;font-weight:600;text-decoration:none;transition:var(--transition);cursor:pointer;border:none;font-family:var(--font)}
.btn-primary{background:var(--gradient-btn);color:#fff;box-shadow:0 4px 24px var(--accent-glow)}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 32px rgba(192,57,43,.4)}
.btn-secondary{background:var(--bg-card);color:var(--text-primary);border:1px solid var(--border-card)}
.btn-secondary:hover{background:var(--bg-card-hover);transform:translateY(-2px)}
.btn-outline{background:transparent;color:var(--accent-3);border:1.5px solid var(--accent-3);padding:12px 28px;border-radius:var(--radius-md);font-size:15px;font-weight:600;text-decoration:none;transition:var(--transition);cursor:pointer;display:inline-flex;align-items:center;gap:8px;font-family:var(--font)}
.btn-outline:hover{background:rgba(192,132,252,.1);transform:translateY(-2px);box-shadow:0 0 24px rgba(192,132,252,.15)}
.btn-sm{padding:8px 16px;font-size:13px}

/* ===== Stats Row ===== */
.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:40px}
.stat-card{background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-lg);padding:22px;text-align:center;backdrop-filter:blur(12px);transition:var(--transition)}
.stat-card:hover{border-color:var(--border-card-hover);transform:translateY(-4px);box-shadow:var(--shadow-card)}
.stat-card .num{font-size:28px;font-weight:800;background:var(--gradient-hero);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-card .label{font-size:12px;color:var(--text-secondary);margin-top:6px;text-transform:uppercase;letter-spacing:1px}
.stat-card .sub{font-size:11px;color:var(--text-muted);margin-top:4px}

/* ===== Panels ===== */
.panel{background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-xl);padding:32px;margin-bottom:30px;backdrop-filter:blur(12px)}
.panel h2{font-size:20px;font-weight:700;margin-bottom:20px;display:flex;align-items:center;gap:10px}
.panel h2 .icon{width:32px;height:32px;background:var(--gradient-btn);border-radius:var(--radius-sm);display:inline-flex;align-items:center;justify-content:center;font-size:16px}

/* ===== Prediction Form ===== */
.pred-form{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.pred-form select,.pred-form button{padding:12px 18px;border-radius:10px;font-size:14px;font-family:var(--font)}
.pred-form select{flex:1;min-width:160px;background:var(--bg-card);border:1px solid var(--border-card);color:var(--text-primary);outline:none;cursor:pointer;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23999' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10z'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 12px center;padding-right:36px}
.pred-form select option{background:#1a0a20;color:var(--text-primary)}
.pred-form button{background:var(--gradient-btn);color:#fff;border:none;font-weight:600;cursor:pointer;transition:var(--transition);white-space:nowrap}
.pred-form button:hover{transform:translateY(-2px);box-shadow:0 8px 24px var(--accent-glow)}
.pred-form button:disabled{opacity:.5;cursor:not-allowed;transform:none}

/* ===== Prediction Result ===== */
#predResult{display:none;background:rgba(255,255,255,.03);border-radius:var(--radius-md);padding:20px;margin-top:16px;border:1px solid rgba(192,57,43,.15)}
#predResult.show{display:block;animation:fadeIn .3s ease}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.pred-nums{display:flex;gap:10px;margin:12px 0;flex-wrap:wrap;align-items:center}
.pred-nums .ball{width:52px;height:52px;border-radius:50%;background:var(--gradient-ball);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:#fff;box-shadow:0 4px 16px rgba(192,57,43,.3);animation:pop .3s ease}
.pred-nums .ball.backup{background:var(--gradient-ball-bu);box-shadow:0 4px 16px rgba(124,58,237,.3)}
@keyframes pop{0%{transform:scale(0)}60%{transform:scale(1.15)}100%{transform:scale(1)}}
.pred-meta{display:flex;gap:12px;flex-wrap:wrap;font-size:13px;color:var(--text-secondary);margin-top:10px}
.pred-meta span{background:var(--bg-card);padding:4px 12px;border-radius:var(--radius-sm)}

/* ===== Market Grid ===== */
.market-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px;max-height:450px;overflow-y:auto;padding-right:8px}
.market-grid::-webkit-scrollbar{width:4px}
.market-grid::-webkit-scrollbar-track{background:transparent}
.market-grid::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:4px}
.market-item{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:var(--bg-card);border-radius:10px;font-size:13px;transition:var(--transition);border:1px solid transparent}
.market-item:hover{background:var(--bg-card-hover);border-color:var(--border-card)}
.market-item .name{font-weight:600;color:#ddd}
.market-item .result{font-weight:700;color:var(--accent-3);font-family:monospace;font-size:15px}
.market-item .period{color:var(--text-muted);font-size:11px}
.search-box{width:100%;padding:10px 14px;border-radius:10px;background:var(--bg-card);border:1px solid var(--border-card);color:var(--text-primary);font-size:13px;font-family:var(--font);outline:none;transition:var(--transition);margin-bottom:12px}
.search-box:focus{border-color:var(--accent-3)}

/* ===== About Grid ===== */
.about-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.about-card{background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-lg);padding:24px;transition:var(--transition)}
.about-card:hover{border-color:var(--border-card-hover);transform:translateY(-2px)}
.about-card h3{font-size:15px;font-weight:600;margin-bottom:8px;color:var(--accent-3)}
.about-card p{font-size:13px;color:var(--text-secondary);line-height:1.6}

/* ===== Input Data ===== */
.input-paste-box{background:var(--bg-card);border:1px dashed var(--border-card-hover);border-radius:var(--radius-md);padding:16px;margin-bottom:16px;transition:var(--transition)}
.input-paste-box:focus-within{border-color:var(--accent-3);box-shadow:0 0 16px rgba(192,132,252,.1)}
.input-paste-box textarea{width:100%;min-height:100px;background:rgba(255,255,255,.03);border:1px solid var(--border-card);border-radius:var(--radius-sm);color:var(--text-primary);font-size:13px;font-family:monospace;padding:12px;outline:none;resize:vertical;transition:var(--transition);line-height:1.5}
.input-paste-box textarea:focus{border-color:var(--accent-3)}
.input-paste-box textarea::placeholder{color:var(--text-muted);font-size:12px}
.input-paste-box .paste-label{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.input-paste-box .paste-label span{font-size:13px;font-weight:600;color:var(--accent-3)}
.input-paste-box .paste-label .hint{font-size:11px;color:var(--text-muted)}
.paste-parse-btn{padding:6px 16px;border-radius:var(--radius-sm);background:var(--gradient-btn);color:#fff;border:none;font-size:12px;font-weight:600;cursor:pointer;transition:var(--transition)}
.paste-parse-btn:hover{transform:translateY(-1px);box-shadow:0 4px 12px var(--accent-glow)}
.input-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px}
.input-box{background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-md);padding:14px 16px;transition:var(--transition)}
.input-box:hover{border-color:var(--border-card-hover)}
.input-box .header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.input-box .market-name{font-weight:700;font-size:14px;color:var(--text-primary)}
.input-box .remove-btn{background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:18px;padding:0 4px;transition:var(--transition)}
.input-box .remove-btn:hover{color:#e74c3c}
.input-fields{display:flex;gap:8px}
.input-fields .field{flex:1}
.input-fields .field label{font-size:11px;color:var(--text-muted);display:block;margin-bottom:2px;text-transform:uppercase;letter-spacing:.5px}
.input-fields .field input{width:100%;padding:8px 10px;border-radius:var(--radius-sm);background:rgba(255,255,255,.06);border:1px solid var(--border-card);color:var(--text-primary);font-size:14px;font-family:var(--font);outline:none;transition:var(--transition)}
.input-fields .field input:focus{border-color:var(--accent-3);box-shadow:0 0 12px rgba(192,132,252,.15)}
.input-fields .field input::placeholder{color:var(--text-muted);font-size:12px}
.input-toolbar{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:16px}
.input-toolbar .date-input{padding:10px 14px;border-radius:var(--radius-sm);background:var(--bg-card);border:1px solid var(--border-card);color:var(--text-primary);font-size:14px;font-family:var(--font);outline:none}
.input-toolbar .date-input:focus{border-color:var(--accent-3)}
.input-toolbar .add-select{padding:10px 14px;border-radius:var(--radius-sm);background:var(--bg-card);border:1px solid var(--border-card);color:var(--text-primary);font-size:13px;font-family:var(--font);outline:none;cursor:pointer;flex:1;min-width:180px}
.input-toolbar .add-select option{background:#1a0a20;color:var(--text-primary)}
.input-summary{font-size:13px;color:var(--text-secondary);margin-top:12px;display:flex;gap:16px;flex-wrap:wrap}
.input-summary span{background:var(--bg-card);padding:6px 14px;border-radius:var(--radius-sm)}
#inputStatus{margin-top:12px;padding:12px 16px;border-radius:var(--radius-sm);font-size:13px;display:none}
#inputStatus.success{display:block;background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.25);color:#10b981}
#inputStatus.error{display:block;background:rgba(231,76,60,.1);border:1px solid rgba(231,76,60,.25);color:#e74c3c}
#inputStatus.sending{display:block;background:rgba(192,132,252,.1);border:1px solid rgba(192,132,252,.25);color:var(--accent-3)}

/* ===== Luna Password Modal ===== */
.modal-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:99999;animation:fadeIn .2s ease}
.modal-box{background:var(--bg-primary);border:1px solid var(--border-card);border-radius:var(--radius-lg);padding:32px;max-width:400px;width:90%;text-align:center;box-shadow:0 24px 64px rgba(0,0,0,.5)}
.modal-box h3{font-size:18px;margin-bottom:8px;color:var(--text-primary)}
.modal-box p{font-size:13px;color:var(--text-secondary);margin-bottom:20px}
.modal-box input[type=password]{width:100%;padding:12px 16px;border-radius:var(--radius-sm);background:rgba(255,255,255,.06);border:2px solid var(--border-card);color:var(--text-primary);font-size:16px;font-family:var(--font);outline:none;text-align:center;letter-spacing:4px;transition:var(--transition)}
.modal-box input[type=password]:focus{border-color:var(--accent-3);box-shadow:0 0 16px rgba(192,132,252,.2)}
.modal-actions{display:flex;gap:12px;justify-content:center;margin-top:20px}
.modal-actions button{padding:10px 24px;border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;border:none;transition:var(--transition)}
.modal-actions .btn-primary{background:var(--gradient-btn);color:#fff}
.modal-actions .btn-primary:hover{transform:translateY(-1px);box-shadow:0 4px 16px var(--accent-glow)}
.modal-actions .btn-secondary{background:var(--bg-card);color:var(--text-secondary)}
.modal-actions .btn-secondary:hover{background:rgba(255,255,255,.1)}
.modal-error{color:#e74c3c;font-size:12px;margin-top:8px;display:none}
/* ===== Luna Results Panel ===== */
.luna-results{margin-top:16px;padding:16px 20px;border-radius:var(--radius-md);background:rgba(16,185,129,.05);border:1px solid rgba(16,185,129,.2);display:none;animation:fadeIn .3s ease}
.luna-results h3{font-size:14px;font-weight:700;color:#10b981;margin-bottom:12px;display:flex;align-items:center;gap:8px}
.luna-results .lr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:6px}
.luna-results .lr-item{display:flex;justify-content:space-between;padding:4px 8px;background:rgba(255,255,255,.03);border-radius:4px;font-size:12px}
.luna-results .lr-item .lr-market{color:var(--text-primary);font-weight:500}
.luna-results .lr-item .lr-result{color:#10b981;font-weight:700}
.luna-results .lr-item .lr-period{color:var(--text-muted)}
.luna-results .lr-summary{margin-top:10px;padding-top:10px;border-top:1px solid rgba(16,185,129,.15);font-size:12px;color:var(--text-secondary);display:flex;gap:16px;flex-wrap:wrap}
.luna-results .lr-summary span{background:rgba(16,185,129,.1);padding:4px 10px;border-radius:4px}
/* ===== Luna Parse Button ===== */
.luna-parse-btn{padding:6px 16px;border-radius:var(--radius-sm);background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;font-size:12px;font-weight:600;cursor:pointer;transition:var(--transition)}
.luna-parse-btn:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(16,185,129,.3)}

/* ===== Footer ===== */
footer{text-align:center;padding:40px 0 20px;border-top:1px solid var(--border-card);margin-top:20px}
footer .links{display:flex;justify-content:center;gap:20px;margin-bottom:16px;flex-wrap:wrap}
footer .links a{color:var(--text-muted);text-decoration:none;font-size:13px;transition:var(--transition)}
footer .links a:hover{color:var(--accent-3)}
footer .copy{color:#444;font-size:12px}

/* ===== Hoki Box ===== */
.hoki-box{margin-top:16px;background:linear-gradient(135deg,rgba(192,57,43,.1),rgba(142,68,173,.1));border:1px solid rgba(192,57,43,.2);border-radius:var(--radius-lg);padding:16px 20px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;transition:var(--transition)}
.hoki-box:hover{border-color:var(--accent-3);box-shadow:0 0 20px rgba(192,132,252,.1)}
.hoki-box .label{font-size:13px;color:var(--text-secondary);display:flex;align-items:center;gap:6px}
.hoki-box .label .icon{font-size:20px}
.hoki-box .nums{display:flex;gap:6px;align-items:center}
.hoki-box .nums .ball{width:36px;height:36px;border-radius:50%;background:var(--gradient-ball);display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;color:#fff;box-shadow:0 2px 10px rgba(192,57,43,.3)}
.hoki-box .nums .ball.bu{background:var(--gradient-ball-bu);box-shadow:0 2px 10px rgba(124,58,237,.3)}
.hoki-box .nums .sep{color:var(--text-muted);font-size:13px;margin:0 4px}
.hoki-box .meta{font-size:11px;color:var(--text-muted)}

/* ===== Utilities ===== */
.spinner{display:inline-block;width:20px;height:20px;border:2px solid rgba(255,255,255,.1);border-top-color:var(--accent-3);border-radius:50%;animation:spin .6s linear infinite;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
.hidden{display:none!important}
.text-center{text-align:center}
.mt-8{margin-top:8px}
.mt-16{margin-top:16px}
.mb-16{margin-bottom:16px}
.gap-8{gap:8px}
.flex{display:flex}
.flex-wrap{flex-wrap:wrap}
.items-center{align-items:center}
.justify-center{justify-content:center}

/* ===== Responsive ===== */
@media(max-width:640px){
  .content{padding:12px}
  .hero{padding:30px 12px 20px}
  .panel{padding:20px}
  .pred-form select{min-width:100%}
  .nav-links a{font-size:12px;padding:6px 10px}
  .logo-text{font-size:18px}
  .clock-time{font-size:clamp(36px,12vw,56px)}
  .stats-row{grid-template-columns:repeat(2,1fr)}
  .about-grid{grid-template-columns:1fr}
  .market-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="bg-orb orb1"></div><div class="bg-orb orb2"></div><div class="bg-orb orb3"></div>

<div class="content">
<!-- ===== Navigation ===== -->
<nav>
  <div class="logo">
    <div class="logo-icon">TG</div>
    <div><div class="logo-text">TGQ</div><div class="logo-sub">Luna Core</div></div>
  </div>
  <div class="nav-links">
    <a href="#home" class="active" data-page="home"><span data-f="home" data-fs="16"></span> Beranda</a>
    <a href="#prediksi" data-page="prediksi"><span data-f="target" data-fs="16"></span> Prediksi</a>
    <a href="#pasar" data-page="pasar"><span data-f="data_bar_vertical" data-fs="16"></span> Pasar</a>
    <a href="#tentang" data-page="tentang"><span data-f="info" data-fs="16"></span> Tentang</a>
    <a href="#input" data-page="input"><span data-f="clipboard_paste" data-fs="16"></span> Input</a>
    <div class="nav-status"><span class="dot"></span><span id="navStatus">Online</span></div>
  </div>
</nav>

<!-- ===== Home Section ===== -->
<section id="home" class="section">
  <div class="hero">
    <div class="hero-badge"><span data-f="sparkle" data-fs="13"></span> PREDIKSI CERDAS BERBASIS DATA</div>
    <h1>Analisis Pola<br>Tanpa Batas</h1>
    <p>TGQ menghadirkan mesin prediksi mutakhir dengan analisis pola real-time dari 46 pasar internasional. Akurat, cepat, dan transparan.</p>
    <div class="hero-actions">
      <a href="#prediksi" class="btn btn-primary" data-nav><span data-f="target" data-fs="18"></span> Coba Prediksi</a>
      <a href="#pasar" class="btn btn-secondary" data-nav><span data-f="globe" data-fs="18"></span> Jelajahi Pasar</a>
    </div>
  </div>

  <!-- Digital Clock -->
  <div class="clock-section">
    <div class="clock-time" id="clockTime">00:00:00</div>
    <div class="clock-date" id="clockDate">—</div>
    <div class="clock-tz">Waktu Indonesia Barat (UTC+7) — Asia/Jakarta</div>
  </div>

  <!-- Stats -->
  <div class="stats-row">
    <div class="stat-card"><div class="num" id="statMarkets">—</div><div class="label">Pasar Aktif</div><div class="sub">Internasional</div></div>
    <div class="stat-card"><div class="num" id="statEngines">—</div><div class="label">Mesin Prediksi</div><div class="sub">AI & Statistik</div></div>
    <div class="stat-card"><div class="num" id="statStatus">—</div><div class="label">Status</div><div class="sub">Server</div></div>
    <div class="stat-card"><div class="num" id="statVersion">—</div><div class="label">Versi API</div><div class="sub">Luna Core</div></div>
  </div>

  <!-- Hoki Number -->
  <div class="hoki-box" id="hokiBox">
    <div class="label"><span class="figlyph fcolor" data-f="sparkle" data-fs="20"></span>Hoki Number Hari Ini</div>
    <div class="nums" id="hokiNums"><span style="color:var(--text-muted);font-size:13px">Memuat...</span></div>
    <div class="meta" id="hokiMeta"></div>
  </div>
</section>

<!-- ===== Prediksi Section ===== -->
<section id="prediksi" class="section hidden">
  <div class="panel">
    <h2><span class="icon"><span data-f="target" data-fs="16"></span></span> Prediksi Cepat</h2>
    <div class="pred-form">
      <select id="engineSelect"></select>
      <select id="marketSelect"></select>
      <button onclick="TGQ.predict()" id="predBtn"><span data-f="sparkle" data-fs="16"></span> Prediksi</button>
    </div>
    <div id="predResult">
      <div style="font-size:14px;color:var(--text-secondary);margin-bottom:4px">Hasil Prediksi</div>
      <div class="pred-nums" id="predNums"></div>
      <div class="pred-meta" id="predMeta"></div>
    </div>
  </div>
</section>

<!-- ===== Pasar Section ===== -->
<section id="pasar" class="section hidden">
  <div class="panel">
    <h2><span class="icon"><span data-f="data_bar_vertical" data-fs="16"></span></span> Pasar Terkini</h2>
    <input class="search-box" id="marketSearch" placeholder="Cari pasar..." oninput="TGQ.filterMarkets()">
    <div style="text-align:right;color:var(--text-muted);font-size:12px;margin-bottom:8px">
      <span id="marketCount">0 pasar</span> ditampilkan
    </div>
    <div class="market-grid" id="marketGrid"></div>
  </div>
</section>

<!-- ===== Tentang Section ===== -->
<section id="tentang" class="section hidden">
  <!-- Promo Hero -->
  <div class="panel" style="text-align:center;padding:48px 32px;border:1px solid rgba(192,57,43,.2);background:linear-gradient(135deg,rgba(192,57,43,.08),rgba(142,68,173,.08))">
    <div class="figlyph lg"><span data-f="target" data-fs="26"></span></div>
    <h2 style="font-size:clamp(24px,3vw,36px);font-weight:900;background:var(--gradient-hero);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px">TGQ — Trust Generator Qualitynumber</h2>
    <p style="font-size:clamp(15px,1.8vw,20px);color:var(--accent-3);font-weight:600;margin-bottom:8px">"From Data to Digits — Precision You Can Trust."</p>
    <p style="font-size:clamp(13px,1.3vw,16px);color:var(--text-secondary);max-width:700px;margin:0 auto 24px;line-height:1.8">
      <strong style="color:var(--text-primary)">TGQ</strong> adalah platform prediksi pasar multi-engine yang mengubah data mentah menjadi angka berkualitas. 
      Bukan feeling, bukan ramalan — <strong style="color:var(--text-primary)">setiap angka lahir dari algoritma</strong> yang terukur, transparan, dan terus berkembang. 
      Dengan <strong style="color:var(--text-primary)">3 engine cerdas</strong> dan cakupan <strong style="color:var(--text-primary)">46 pasar global</strong>, 
      TGQ hadir untuk memberikan keunggulan prediksi yang nyata.
    </p>
    <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap;font-size:13px;color:var(--text-muted)">
      <span class="figlyph fcolor" data-f="bot" data-fs="14"></span><strong style="color:var(--accent-3)">3 Mesin</strong> Prediksi
      <span class="figlyph fcolor" data-f="globe" data-fs="14"></span><strong style="color:var(--accent-3)">46</strong> Pasar Global
      <span class="figlyph fcolor" data-f="timer" data-fs="14"></span><strong style="color:var(--accent-3)">Detik</strong> Hasil
      <span class="figlyph fcolor" data-f="checkmark_circle" data-fs="14"></span><strong style="color:var(--accent-3)">100%</strong> Transparan
      <span class="figlyph fcolor" data-f="data_bar_vertical" data-fs="14"></span><strong style="color:var(--accent-3)">Data-Driven</strong>
    </div>
  </div>

  <!-- Feature Cards -->
  <div class="about-grid">
    <div class="about-card" style="border-left:3px solid #c0392b">
      <div class="figlyph fcolor" style="margin-bottom:8px" data-f="bot" data-fs="32"></div>
      <h3>3 Engine Prediksi Canggih</h3>
      <p>TGQ ditenagai <strong>tiga algoritma</strong> yang saling melengkapi: <strong>Toto Macau</strong> (Similarity + Frequency Analysis), <strong>Oregon</strong> (Pattern Recognition), dan <strong>Historical Trend</strong> (Analisis Gelombang Sejarah). Bukan satu mesin — tapi <strong>satu arsenal prediksi</strong>.</p>
    </div>
    <div class="about-card" style="border-left:3px solid #8e44ad">
      <div class="figlyph fcolor" style="margin-bottom:8px" data-f="globe" data-fs="32"></div>
      <h3>46 Pasar — Satu Platform</h3>
      <p>Dari <strong>Toto Macau 4D/5D/6D</strong>, Oregon, Singapore, PCSO, Bangkok, Brunei, Bullseye, California, Carolina, Chelsea, Florida, Jakarta, Kentucky, <strong>KingKong4D</strong>, Magnum4D, Nevada, New York, Huahin, Poipet, Totomali, Hongkong Lotto — <strong>semua terpantau real-time</strong>. Satu pintu untuk semua pasar.</p>
    </div>
    <div class="about-card" style="border-left:3px solid #f59e0b">
      <div class="figlyph fcolor" style="margin-bottom:8px" data-f="timer" data-fs="32"></div>
      <h3>Real-Time. Cepat. Akurat.</h3>
      <p>Hasil prediksi dalam <strong>hitungan detik</strong> — bukan menit, bukan jam. Setiap prediksi menyertakan <strong>confidence score</strong>, analisis digit frequency, similarity mapping, dan metode yang digunakan. <strong>Kecepatan tanpa mengorbankan kualitas.</strong></p>
    </div>
    <div class="about-card" style="border-left:3px solid #10b981">
      <div class="figlyph fcolor" style="margin-bottom:8px" data-f="search" data-fs="32"></div>
      <h3>Transparan & Bisa Diaudit</h3>
      <p>Tidak ada kotak hitam. <strong>Setiap angka bisa dilacak asal-usulnya</strong> — data sumber, algoritma, perhitungan. API terdokumentasi lengkap, source markets terbuka. <strong>TGQ adalah open-book prediction.</strong></p>
    </div>
    <div class="about-card" style="border-left:3px solid #3b82f6">
      <div class="figlyph fcolor" style="margin-bottom:8px" data-f="rocket" data-fs="32"></div>
      <h3>Multi-Platform, Siap Kapan Saja</h3>
      <p>Akses TGQ dari mana saja: <strong>Note 8 Server</strong> (local 24/7) dengan backup <strong>GitHub Pages</strong>. Prediksi tak pernah berhenti.</p>
    </div>
    <div class="about-card" style="border-left:3px solid #f43f5e">
      <div class="figlyph fcolor" style="margin-bottom:8px" data-f="trophy" data-fs="32"></div>
      <h3>Dibangun oleh Mr.2211</h3>
      <p>TGQ adalah buah karya <strong>Mr.2211</strong> — dikembangkan dari <strong>Samsung Galaxy Note 8</strong> sebagai server produksi yang berjalan 24/7. Setiap baris kode adalah dedikasi nyata untuk menciptakan <strong>sistem prediksi transparan, akurat, dan bisa diakses semua orang.</strong> Bukan proyek biasa — ini <strong>Trust Generator Qualitynumber.</strong></p>
    </div>
  </div>

  <!-- CTA Banner -->
  <div class="panel" style="text-align:center;margin-top:20px;background:linear-gradient(135deg,rgba(192,57,43,.1),rgba(142,68,173,.1));border:1px solid rgba(192,57,43,.15)">
    <p style="font-size:18px;font-weight:600;margin-bottom:4px"><span class="figlyph fcolor" data-f="sparkle" data-fs="18"></span> Angka Bukan Lagi Tebakan</p>
    <p style="font-size:14px;color:var(--text-secondary);margin-bottom:16px;font-style:italic">"From Data to Digits — Precision You Can Trust."</p>
    <div class="hero-actions">
      <a href="#prediksi" class="btn btn-primary" data-nav><span data-f="target" data-fs="18"></span> Mulai Prediksi</a>
      <a href="#pasar" class="btn btn-secondary" data-nav><span data-f="globe" data-fs="18"></span> Jelajahi 46 Pasar</a>
    </div>
    <p style="font-size:11px;color:var(--text-muted);margin-top:16px">© 2026 Mr.2211 — TGQ Trust Generator Qualitynumber</p>
  </div>
</section>

<!-- ===== Input Data Section ===== -->
<section id="input" class="section hidden">
  <div class="panel">
    <h2><span class="icon"><span data-f="edit" data-fs="16"></span></span> Input Data Pasar</h2>
    <p style="font-size:13px;color:var(--text-secondary);margin-bottom:16px">
      Masukkan hasil result & periode untuk setiap pasar. Data akan dikirim ke server pusat untuk diproses engine prediksi.
    </p>

    <!-- Luna Paste Here -->
    <div class="input-paste-box">
      <div class="paste-label">
        <span><span class="figlyph fcolor" data-f="clipboard_paste" data-fs="16"></span> Luna paste here</span>
        <div>
          <span class="hint">Paste text dari data_harian → otomatis isi box di bawah</span>
          <button class="paste-parse-btn" onclick="TGQ.parsePaste()" style="margin-left:10px"><span data-f="send" data-fs="13"></span> Parse</button>
          <button class="luna-parse-btn" onclick="TGQ.showLunaModal()" style="margin-left:6px"><span data-f="key" data-fs="13"></span> Luna Parse</button>
        </div>
      </div>
      <textarea id="lunaPaste" placeholder="Contoh:
5D TOTO MACAU POOL
06510
[PERIODE : 3463]

4D TOTO MACAU POOL
7377
[PERIODE : 13772]

KING KONG 4D POOL
7349
[PERIODE : 1926]" onpaste="setTimeout(()=>TGQ.parsePaste(),100)"></textarea>
    </div>

    <!-- Toolbar -->
    <div class="input-toolbar">
      <input class="date-input" id="inputDate" type="date" style="color-scheme:dark">
      <select class="add-select" id="addMarketSelect">
        <option value="">+ Tambah pasar...</option>
      </select>
      <button class="btn btn-primary" onclick="TGQ.submitInput()" id="submitInputBtn" style="padding:10px 20px;font-size:13px"><span data-f="send" data-fs="15"></span> Kirim Data</button>
      <button class="btn btn-secondary" onclick="TGQ.clearInput()" style="padding:10px 20px;font-size:13px"><span data-f="delete" data-fs="15"></span> Reset</button>
    </div>

    <!-- Luna Password Modal -->
    <div id="lunaModal" class="modal-overlay" style="display:none">
      <div class="modal-box">
        <h3><span class="figlyph fcolor" data-f="key" data-fs="18"></span> Selamat datang Mr.2211</h3>
        <p>Harap masukkan password untuk melanjutkan</p>
        <input type="password" id="lunaPassword" placeholder="Masukkan password..." onkeydown="if(event.key==='Enter')TGQ.lunaParse()">
        <div class="modal-error" id="lunaPasswordError"><span class="figlyph" data-f="error_circle" data-fs="14"></span> Password salah!</div>
        <div class="modal-actions">
          <button class="btn-secondary" onclick="TGQ.closeLunaModal()">Batal</button>
          <button class="btn-primary" onclick="TGQ.lunaParse()"><span data-f="key" data-fs="14"></span> Masuk</button>
        </div>
      </div>
    </div>

    <!-- Input Grid -->
    <div class="input-grid" id="inputGrid"></div>

    <!-- Summary -->
    <div class="input-summary">
      <span><span class="figlyph fcolor" data-f="box" data-fs="14"></span> <span id="inputCount">0</span> pasar diisi</span>
      <span><span class="figlyph fcolor" data-f="checkmark" data-fs="14"></span> <span id="filledCount">0</span> siap kirim</span>
    </div>

    <!-- Status -->
    <div id="inputStatus"></div>

    <!-- Luna Results -->
    <div class="luna-results" id="lunaResults">
      <h3><span data-f="data_bar_vertical" data-fs="16"></span> Hasil Ekstraksi Luna Parse</h3>
      <div class="lr-grid" id="lunaResultsGrid"></div>
      <div class="lr-summary" id="lunaResultsSummary"></div>
    </div>
  </div>
</section>

<!-- ===== Footer ===== -->
<footer>
  <div class="links">
    <a href="#home" data-nav>Beranda</a>
    <a href="#prediksi" data-nav>Prediksi</a>
    <a href="#pasar" data-nav>Pasar</a>
    <a href="#tentang" data-nav>Tentang</a>
    <a href="#input" data-nav>Input Data</a>
    <a href="/api/docs" target="_blank">API Docs</a>
  </div>
  <div class="copy">© 2026 TGQ — Luna Core. All rights reserved.</div>
<div class="copy" style="margin-top:8px;font-size:11px;color:#555"><span class="figlyph fcolor" data-f="globe" data-fs="12"></span> GitHub Pages backup · <span class="figlyph fcolor" data-f="timer" data-fs="12"></span> Waktu lokal · <span class="figlyph fcolor" data-f="rocket" data-fs="12"></span> API via Note 8</div>
</footer>
</div>

<script>
/* ============================================================
   TGQ — Fluent UI System Icons
   Microsoft Fluent icon set, injected inline (currentColor).
   ============================================================ */
const ICONS = {
    'add': ['M12 3.25c.41 0 .75.34.75.75v7.25H20a.75.75 0 0 1 0 1.5h-7.25V20a.75.75 0 0 1-1.5 0v-7.25H4a.75.75 0 0 1 0-1.5h7.25V4c0-.41.34-.75.75-.75Z'],
    'arrow_left': ['M10.73 19.8a.75.75 0 0 0 1.04-1.1l-6.25-5.95h14.73a.75.75 0 0 0 0-1.5H5.52l6.25-5.95a.75.75 0 0 0-1.04-1.1l-7.42 7.08a1 1 0 0 0 0 1.44l7.42 7.07Z'],
    'arrow_right': ['M13.27 4.2a.75.75 0 0 0-1.04 1.1l6.25 5.95H3.75a.75.75 0 0 0 0 1.5h14.73l-6.25 5.95a.75.75 0 0 0 1.04 1.1l7.42-7.08a1 1 0 0 0 0-1.44L13.27 4.2Z'],
    'arrow_upload': ['M18.25 3.51a.75.75 0 1 0 0-1.5h-13a.75.75 0 1 0 0 1.5h13ZM11.65 22h.1c.38 0 .7-.28.74-.64l.01-.1V7.56l3.72 3.72c.27.27.68.29.98.07l.08-.07a.75.75 0 0 0 .07-.98l-.07-.08-5-5a.75.75 0 0 0-.97-.07l-.09.07-5 5a.75.75 0 0 0 .98 1.13l.08-.07L11 7.58v13.67c0 .38.28.7.65.75Z'],
    'bot': ['M17.75 14C19 14 20 15 20 16.25v.9c0 1.1-.47 2.14-1.3 2.85-1.57 1.34-3.81 2-6.7 2s-5.13-.66-6.7-2A3.75 3.75 0 0 1 4 17.16v-.91C4 15 5.01 14 6.25 14h11.5Zm0 1.5H6.25a.75.75 0 0 0-.75.75v.9c0 .66.29 1.29.79 1.71C7.55 19.94 9.44 20.5 12 20.5s4.46-.56 5.72-1.64c.5-.43.78-1.05.78-1.7v-.91a.75.75 0 0 0-.75-.75ZM11.9 2h.1c.38 0 .7.28.74.65l.01.1v.75h3.5c1.24 0 2.25 1 2.25 2.25v4.5c0 1.25-1 2.25-2.25 2.25h-8.5c-1.24 0-2.25-1-2.25-2.25v-4.5c0-1.24 1-2.25 2.25-2.25h3.5v-.75c0-.38.28-.7.65-.74L12 2h-.1Zm4.35 3h-8.5a.75.75 0 0 0-.75.75v4.5c0 .42.34.75.75.75h8.5c.41 0 .75-.33.75-.75v-4.5a.75.75 0 0 0-.75-.75Zm-6.5 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5Zm4.5 0a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5Z'],
    'box': ['M10.6 2.51c.9-.36 1.9-.36 2.8 0l7.5 3.04c.67.27 1.1.91 1.1 1.62v9.66c0 .71-.43 1.35-1.1 1.62l-7.5 3.04c-.9.37-1.9.37-2.8 0l-7.5-3.04c-.67-.27-1.1-.91-1.1-1.62V7.17c0-.7.43-1.35 1.1-1.62l7.5-3.04Zm2.25 1.4a2.25 2.25 0 0 0-1.7 0l-1.9.77 7.52 2.93 2.67-1.03-6.6-2.68Zm1.84 4.5L7.21 5.5 4.6 6.56 12 9.45l2.7-1.04ZM3.5 16.83c0 .1.06.2.16.23l7.5 3.04.09.04v-9.38L3.5 7.75v9.08Zm9.35 3.27 7.5-3.04c.09-.04.15-.13.15-.23V7.77l-7.75 3v9.37l.1-.04Z'],
    'calculator': ['M7 7c0-1.1.9-2 2-2h6a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V7Zm2-.5a.5.5 0 0 0-.5.5v1c0 .28.22.5.5.5h6a.5.5 0 0 0 .5-.5V7a.5.5 0 0 0-.5-.5H9Zm-.75 8a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5Zm1.25 2.75a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0Zm6.25-2.75a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5ZM17 17.25a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0Zm-5-2.75a1.25 1.25 0 1 0 0-2.5 1.25 1.25 0 0 0 0 2.5Zm1.25 2.75a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0ZM7.25 2A3.25 3.25 0 0 0 4 5.25v13.5C4 20.55 5.46 22 7.25 22h9.5c1.8 0 3.25-1.46 3.25-3.25V5.25C20 3.45 18.54 2 16.75 2h-9.5ZM5.5 5.25c0-.97.78-1.75 1.75-1.75h9.5c.97 0 1.75.78 1.75 1.75v13.5c0 .97-.78 1.75-1.75 1.75h-9.5c-.97 0-1.75-.78-1.75-1.75V5.25Z'],
    'chart_person': ['M12.5 2.75a.75.75 0 0 0-1.5 0V3H5.25A3.25 3.25 0 0 0 2 6.25v9.5C2 17.55 3.46 19 5.25 19h2.4l-1.48 1.77a.75.75 0 0 0 1.16.96L9.6 19h3.5c.19-.61.57-1.14 1.08-1.5H5.25c-.97 0-1.75-.78-1.75-1.75v-9.5c0-.97.78-1.75 1.75-1.75h13.5c.97 0 1.75.78 1.75 1.75v5.38A3.5 3.5 0 0 1 22 14.5V6.25C22 4.45 20.54 3 18.75 3H12.5v-.25Zm-6.5 5c0-.41.34-.75.75-.75h4a.75.75 0 0 1 0 1.5h-4A.75.75 0 0 1 6 7.75ZM6.75 10a.75.75 0 0 0 0 1.5h6.5a.75.75 0 0 0 0-1.5h-6.5ZM6 13.75c0-.41.34-.75.75-.75h5.5a.75.75 0 0 1 0 1.5h-5.5a.75.75 0 0 1-.75-.75Zm15 .75a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0Zm2 5.38c0 1.55-1.29 3.12-4.5 3.12S14 21.44 14 19.87v-.1c0-.98.8-1.77 1.77-1.77h5.46c.98 0 1.77.8 1.77 1.77v.1Z'],
    'checkmark': ['M4.53 12.97a.75.75 0 0 0-1.06 1.06l4.5 4.5c.3.3.77.3 1.06 0l11-11a.75.75 0 0 0-1.06-1.06L8.5 16.94l-3.97-3.97Z'],
    'checkmark_circle': ['M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20Zm0 1.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Zm-1.25 9.94 4.47-4.47a.75.75 0 0 1 1.13.98l-.07.08-5 5a.75.75 0 0 1-.98.07l-.08-.07-2.5-2.5a.75.75 0 0 1 .98-1.13l.08.07 1.97 1.97 4.47-4.47-4.47 4.47Z'],
    'clipboard_paste': ['M12.75 2c1.16 0 2.11.88 2.24 2h1.76c1.2 0 2.17.93 2.24 2.1l.01.15c0 .38-.28.7-.65.74h-.1a.75.75 0 0 1-.74-.64l-.01-.1c0-.38-.28-.7-.65-.74l-.1-.01h-2.13c-.4.6-1.09 1-1.87 1h-3.5c-.78 0-1.46-.4-1.87-1H5.25c-.38 0-.7.28-.74.65l-.01.1v13.5c0 .38.28.7.65.75h3.1c.38 0 .7.29.74.65l.01.1c0 .42-.34.75-.75.75h-3c-1.2 0-2.17-.92-2.24-2.1L3 19.76V6.25c0-1.2.93-2.17 2.1-2.24L5.25 4h1.76c.13-1.12 1.08-2 2.24-2h3.5Zm6 6c1.2 0 2.17.93 2.24 2.1l.01.15v9.5c0 1.2-.93 2.17-2.1 2.24l-.15.01h-6.5c-1.2 0-2.17-.93-2.24-2.1l-.01-.15v-9.5c0-1.2.93-2.17 2.1-2.24l.15-.01h6.5Zm0 1.5h-6.5c-.38 0-.7.28-.74.65l-.01.1v9.5c0 .38.28.7.65.74l.1.01h6.5c.38 0 .7-.28.74-.65l.01-.1v-9.5c0-.38-.28-.7-.65-.74l-.1-.01Zm-6-6h-3.5a.75.75 0 0 0 0 1.5h3.5a.75.75 0 1 0 0-1.5Z'],
    'data_bar_vertical': ['M5.75 3C6.99 3 8 4 8 5.25v13.5a2.25 2.25 0 1 1-4.5 0V5.25C3.5 4 4.5 3 5.75 3Zm6.5 4c1.24 0 2.25 1 2.25 2.25v9.5a2.25 2.25 0 1 1-4.5 0v-9.5C10 8 11 7 12.25 7Zm6.5 4c1.24 0 2.25 1 2.25 2.25v5.5a2.25 2.25 0 1 1-4.5 0v-5.5c0-1.24 1-2.25 2.25-2.25Zm-13-6.5a.75.75 0 0 0-.75.75v13.5a.75.75 0 0 0 1.5 0V5.25a.75.75 0 0 0-.75-.75Zm6.5 4a.75.75 0 0 0-.75.75v9.5a.75.75 0 0 0 1.5 0v-9.5a.75.75 0 0 0-.75-.75Zm6.5 4a.75.75 0 0 0-.75.75v5.5a.75.75 0 0 0 1.5 0v-5.5a.75.75 0 0 0-.75-.75Z'],
    'database': ['M4 6c0-.7.32-1.3.77-1.78a5.61 5.61 0 0 1 1.8-1.2A13.65 13.65 0 0 1 12 2c2.08 0 4 .38 5.43 1.02.72.32 1.34.72 1.8 1.2.45.49.77 1.09.77 1.78v12c0 .7-.32 1.3-.77 1.78-.46.48-1.08.88-1.8 1.2A13.65 13.65 0 0 1 12 22c-2.08 0-4-.38-5.43-1.02a5.61 5.61 0 0 1-1.8-1.2A2.6 2.6 0 0 1 4 18V6Zm1.5 0c0 .2.09.46.37.75.27.3.71.6 1.31.86 1.2.54 2.9.89 4.82.89 1.92 0 3.62-.35 4.82-.89.6-.26 1.04-.56 1.31-.86.28-.3.37-.54.37-.75 0-.2-.09-.46-.37-.75-.27-.3-.71-.6-1.31-.86-1.2-.54-2.9-.89-4.82-.89-1.92 0-3.62.35-4.82.89-.6.26-1.04.56-1.31.86-.28.3-.37.54-.37.75Zm13 2.4a6.8 6.8 0 0 1-1.07.58A13.65 13.65 0 0 1 12 10c-2.08 0-4-.38-5.43-1.02A6.8 6.8 0 0 1 5.5 8.4V18c0 .2.09.46.37.75.27.3.71.6 1.31.86 1.2.54 2.9.89 4.82.89 1.92 0 3.62-.35 4.82-.89.6-.26 1.04-.56 1.31-.86.28-.3.37-.54.37-.75V8.4Z'],
    'delete': ['M10 5h4a2 2 0 1 0-4 0ZM8.5 5a3.5 3.5 0 1 1 7 0h5.75a.75.75 0 0 1 0 1.5h-1.32l-1.17 12.11A3.75 3.75 0 0 1 15.03 22H8.97a3.75 3.75 0 0 1-3.73-3.39L4.07 6.5H2.75a.75.75 0 0 1 0-1.5H8.5Zm2 4.75a.75.75 0 0 0-1.5 0v7.5a.75.75 0 0 0 1.5 0v-7.5ZM14.25 9c.41 0 .75.34.75.75v7.5a.75.75 0 0 1-1.5 0v-7.5c0-.41.34-.75.75-.75Zm-7.52 9.47a2.25 2.25 0 0 0 2.24 2.03h6.06c1.15 0 2.12-.88 2.24-2.03L18.42 6.5H5.58l1.15 11.97Z'],
    'dismiss': ['m4.4 4.55.07-.08a.75.75 0 0 1 .98-.07l.08.07L12 10.94l6.47-6.47a.75.75 0 1 1 1.06 1.06L13.06 12l6.47 6.47c.27.27.3.68.07.98l-.07.08a.75.75 0 0 1-.98.07l-.08-.07L12 13.06l-6.47 6.47a.75.75 0 0 1-1.06-1.06L10.94 12 4.47 5.53a.75.75 0 0 1-.07-.98l.07-.08-.07.08Z'],
    'document': ['M6 2a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12a2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L13.6 2.6A2 2 0 0 0 12.17 2H6Zm-.5 2c0-.28.22-.5.5-.5h6V8c0 1.1.9 2 2 2h4.5v10a.5.5 0 0 1-.5.5H6a.5.5 0 0 1-.5-.5V4Zm11.88 4.5H14a.5.5 0 0 1-.5-.5V4.62l3.88 3.88Z'],
    'edit': ['M20.95 3.05a3.58 3.58 0 0 0-5.06 0L3.94 15c-.4.4-.7.92-.82 1.48l-1.1 4.6a.75.75 0 0 0 .9.9l4.6-1.1A3.1 3.1 0 0 0 9 20.07L20.95 8.11a3.58 3.58 0 0 0 0-5.06Zm-4 1.06a2.08 2.08 0 1 1 2.94 2.94l-.89.89L16.06 5l.9-.9ZM15 6.06 17.94 9l-10 10a1.6 1.6 0 0 1-.76.43l-3.42.8.82-3.4c.06-.3.21-.56.42-.77l10-10Z'],
    'error_circle': ['M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20Zm0 1.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Zm0 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2ZM12 7c.37 0 .69.28.74.65v4.6a.75.75 0 0 1-1.48.1l-.01-.1v-4.5c0-.41.33-.75.74-.75Z'],
    'fire': ['M12.54 4.3c.32-.25.64-.44.93-.57.09 2.13 1.13 3.73 2.13 5.14l.27.38c1.08 1.52 2.01 2.82 2.11 4.54a6.86 6.86 0 0 1-1.33 4.83 5.43 5.43 0 0 1-4.4 1.88c-2.06 0-3.61-.53-4.7-1.42a5.83 5.83 0 0 1-1.98-3.87 5.56 5.56 0 0 1 .86-4l.32.6a2.2 2.2 0 0 0 2.9.96c1.3-.62 1.58-2.21 1.17-3.33a3.94 3.94 0 0 1-.11-2.7 5.32 5.32 0 0 1 1.83-2.45ZM6.16 9.31h-.01l-.01.02a1.94 1.94 0 0 0-.13.1c-.07.07-.18.16-.3.3-.24.24-.55.62-.83 1.12a7.06 7.06 0 0 0-.8 4.55c.27 2 1.1 3.67 2.53 4.83C8.02 21.4 9.94 22 12.25 22c2.39 0 4.3-.9 5.55-2.43a8.35 8.35 0 0 0 1.68-5.86c-.13-2.18-1.31-3.83-2.36-5.29l-.3-.42C15.68 6.4 14.78 4.9 15 2.83a.75.75 0 0 0-.75-.83c-.38 0-.82.12-1.24.3a6.82 6.82 0 0 0-3.72 3.96c-.49 1.4-.24 2.73.12 3.7.24.64-.02 1.27-.4 1.46a.7.7 0 0 1-.93-.31l-.81-1.54a.75.75 0 0 0-1.11-.25Z'],
    'gift': ['M14.5 2a3.25 3.25 0 0 1 2.74 5h2.51c.69 0 1.25.56 1.25 1.25v3.5c0 .6-.43 1.1-1 1.22v5.78a3.25 3.25 0 0 1-3.07 3.24l-.18.01h-9.5a3.25 3.25 0 0 1-3.24-3.07L4 18.75v-5.78c-.57-.11-1-.62-1-1.22v-3.5C3 7.56 3.56 7 4.25 7h2.51A3.25 3.25 0 0 1 12 3.17C12.6 2.46 13.5 2 14.5 2Zm-3.25 11H5.5v5.75c0 .92.7 1.67 1.6 1.74l.15.01h4V13Zm7.25 0h-5.75v7.5h4c.92 0 1.67-.7 1.74-1.6l.01-.15V13Zm-7.25-4.5H4.5v3h6.75v-3Zm8.25 3v-3h-6.75v3h6.75Zm-5-8c-.97 0-1.75.78-1.75 1.75V7H14.64a1.75 1.75 0 0 0-.14-3.5Zm-5 0A1.75 1.75 0 0 0 9.36 7H11.25V5.1c-.08-.9-.83-1.61-1.75-1.61Z'],
    'globe': ['M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20Zm2.94 14.5H9.06c.65 2.41 1.79 4 2.94 4s2.29-1.59 2.94-4Zm-7.43 0H4.79a8.53 8.53 0 0 0 4.09 3.41c-.52-.82-.95-1.85-1.27-3.02l-.1-.39Zm11.7 0H16.5c-.32 1.33-.79 2.5-1.37 3.41a8.53 8.53 0 0 0 3.9-3.13l.2-.28ZM7.1 10H3.74v.02a8.52 8.52 0 0 0 .3 4.98h3.18a20.3 20.3 0 0 1-.13-5Zm8.3 0H8.6a18.97 18.97 0 0 0 .14 5h6.52a18.5 18.5 0 0 0 .14-5Zm4.87 0h-3.35a20.85 20.85 0 0 1-.13 5h3.18a8.48 8.48 0 0 0 .3-5ZM8.88 4.09h-.02a8.53 8.53 0 0 0-4.61 4.4l3.05.01c.31-1.75.86-3.28 1.58-4.41Zm3.12-.6-.12.01c-1.26.12-2.48 2.12-3.05 5h6.34c-.56-2.87-1.78-4.87-3.04-5H12Zm3.12.6.1.17A12.64 12.64 0 0 1 16.7 8.5h3.05a8.53 8.53 0 0 0-4.34-4.29l-.29-.12Z'],
    'heart': ['M12.82 5.58 12 6.4l-.82-.82a5.37 5.37 0 1 0-7.6 7.6l7.89 7.9c.3.29.77.29 1.06 0l7.9-7.9a5.38 5.38 0 1 0-7.61-7.6Zm6.55 6.54L12 19.48l-7.36-7.36a3.87 3.87 0 1 1 5.48-5.48L11.47 8c.3.3.79.29 1.08-.02l1.33-1.34a3.88 3.88 0 0 1 5.49 5.48Z'],
    'history': ['M12 4.5a7.5 7.5 0 1 1-7.42 6.4c.07-.46-.26-.9-.72-.9-.37 0-.7.26-.76.62A9 9 0 1 0 6 5.3V4.25a.75.75 0 0 0-1.5 0v3c0 .41.34.75.75.75h3a.75.75 0 0 0 0-1.5H6.9a7.47 7.47 0 0 1 5.1-2Zm.5 3.25a.75.75 0 0 0-1.5 0v4.5c0 .41.34.75.75.75h3a.75.75 0 0 0 0-1.5H12.5V7.75Z'],
    'home': ['M10.55 2.53c.84-.7 2.06-.7 2.9 0l6.75 5.7c.5.42.8 1.05.8 1.71v9.31c0 .97-.78 1.75-1.75 1.75h-3.5c-.97 0-1.75-.78-1.75-1.75v-5a.25.25 0 0 0-.25-.25h-3.5a.25.25 0 0 0-.25.25v5c0 .97-.78 1.75-1.75 1.75h-3.5C3.78 21 3 20.22 3 19.25v-9.3c0-.67.3-1.3.8-1.73l6.75-5.69Zm1.93 1.15a.75.75 0 0 0-.96 0l-6.75 5.7a.75.75 0 0 0-.27.56v9.31c0 .14.11.25.25.25h3.5c.14 0 .25-.1.25-.25v-5c0-.97.78-1.75 1.75-1.75h3.5c.97 0 1.75.78 1.75 1.75v5c0 .14.11.25.25.25h3.5c.14 0 .25-.1.25-.25v-9.3c0-.23-.1-.44-.27-.58l-6.75-5.7Z'],
    'info': ['M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20Zm0 1.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Zm0 7c.41 0 .75.34.75.75v5a.75.75 0 0 1-1.5 0v-5c0-.41.34-.75.75-.75ZM12 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z'],
    'key': ['M18.25 7a1.25 1.25 0 1 1-2.5 0 1.25 1.25 0 0 1 2.5 0ZM15.5 2.05A6.55 6.55 0 0 0 9.06 9.7c.02.1-.02.2-.07.25l-6.24 6.23c-.51.52-.8 1.22-.8 1.95v2.17c0 .97.78 1.75 1.75 1.75h2.5c.97 0 1.75-.78 1.75-1.75v-1.25H9.7c.69 0 1.25-.56 1.25-1.25v-1.75h1.75c.67 0 1.22-.54 1.25-1.2a6.55 6.55 0 0 0 8.1-6.35 6.47 6.47 0 0 0-6.55-6.45ZM10.45 8.6a5.05 5.05 0 0 1 5.05-5.05c2.8 0 5.05 2.18 5.05 4.95a5.05 5.05 0 0 1-7.06 4.61.75.75 0 0 0-1.04.69v.75H10.7c-.7 0-1.25.56-1.25 1.25v1.75H7.7c-.7 0-1.25.56-1.25 1.25v1.5c0 .14-.11.25-.25.25H3.7a.25.25 0 0 1-.25-.25v-2.17c0-.33.13-.65.37-.89l6.23-6.23c.42-.42.58-1 .49-1.57-.06-.3-.1-.58-.1-.84Z'],
    'money': ['M10.5 8a3 3 0 1 0 0 6 3 3 0 0 0 0-6ZM9 11a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM2 7.25C2 6.01 3 5 4.25 5h12.5C17.99 5 19 6 19 7.25v7.5c0 1.24-1 2.25-2.25 2.25H4.25C3.01 17 2 16 2 14.75v-7.5Zm2.25-.75a.75.75 0 0 0-.75.75V8h.75c.41 0 .75-.34.75-.75V6.5h-.75Zm-.75 6h.75c1.24 0 2.25 1 2.25 2.25v.75h8v-.75c0-1.24 1-2.25 2.25-2.25h.75v-3h-.75c-1.24 0-2.25-1-2.25-2.25V6.5h-8v.75c0 1.24-1 2.25-2.25 2.25H3.5v3Zm14-4.5v-.75a.75.75 0 0 0-.75-.75H16v.75c0 .41.34.75.75.75h.75Zm0 6h-.75a.75.75 0 0 0-.75.75v.75h.75c.41 0 .75-.34.75-.75V14Zm-14 .75c0 .41.34.75.75.75H5v-.75a.75.75 0 0 0-.75-.75H3.5v.75Zm.9 3.75A3 3 0 0 0 7 20h10.25A4.75 4.75 0 0 0 22 15.25V10a3 3 0 0 0-1.5-2.6v7.85c0 1.8-1.46 3.25-3.25 3.25H4.4Z'],
    'number_symbol': ['M10.99 2.89a.75.75 0 1 0-1.48-.28L8.5 8H3.75a.75.75 0 1 0 0 1.5h4.46l-.95 5H2.75a.75.75 0 0 0 0 1.5h4.23l-.97 5.11a.75.75 0 1 0 1.48.28L8.5 16h5.47l-.97 5.12a.75.75 0 1 0 1.48.28L15.5 16h4.74a.75.75 0 1 0 0-1.5h-4.46l.95-5h4.51a.75.75 0 1 0 0-1.5h-4.23L18 2.9a.75.75 0 0 0-1.48-.28L15.5 8h-5.47L11 2.9Zm-1.25 6.6h5.47l-.94 5H8.79l.95-5Z'],
    'open': ['M6.25 4.5c-.97 0-1.75.78-1.75 1.75v11.5c0 .97.78 1.75 1.75 1.75h11.5c.97 0 1.75-.78 1.75-1.75v-4a.75.75 0 0 1 1.5 0v4c0 1.8-1.46 3.25-3.25 3.25H6.25A3.25 3.25 0 0 1 3 17.75V6.25C3 4.45 4.46 3 6.25 3h4a.75.75 0 0 1 0 1.5h-4ZM13 3.75c0-.41.34-.75.75-.75h6.5c.41 0 .75.34.75.75v6.5a.75.75 0 0 1-1.5 0V5.56l-5.22 5.22a.75.75 0 0 1-1.06-1.06l5.22-5.22h-4.69a.75.75 0 0 1-.75-.75Z'],
    'people': ['M5.5 8a2.5 2.5 0 1 1 5 0 2.5 2.5 0 0 1-5 0ZM8 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm7.5 5a1.5 1.5 0 1 1 3 0 1.5 1.5 0 0 1-3 0ZM17 6a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm-2.75 13.04c.7.28 1.6.46 2.75.46 2.28 0 3.59-.7 4.3-1.56a3.14 3.14 0 0 0 .7-1.73v-.03c0-1.2-.97-2.18-2.18-2.18H14.1c.4.41.68.93.81 1.5h4.91a.68.68 0 0 1 .68.7l-.04.18c-.04.16-.13.38-.32.6C19.8 17.42 18.97 18 17 18c-.98 0-1.67-.15-2.17-.34-.1.4-.28.88-.58 1.38ZM4.25 14C3.01 14 2 15 2 16.25v.28a2.07 2.07 0 0 0 .01.2c.02.14.04.32.1.53.09.42.29.98.68 1.55C3.61 19.97 5.17 21 8 21s4.39-1.03 5.2-2.2a4.48 4.48 0 0 0 .8-2.27v-.28c0-1.24-1-2.25-2.25-2.25h-7.5Zm-.75 2.5v-.25c0-.41.34-.75.75-.75h7.5c.41 0 .75.34.75.75v.34l-.06.33c-.07.28-.2.65-.46 1.02-.5.71-1.56 1.56-3.98 1.56s-3.49-.85-3.98-1.56a2.99 2.99 0 0 1-.52-1.43Z'],
    'rocket': ['M13.06 7.43a2.5 2.5 0 1 1 3.53 3.54 2.5 2.5 0 0 1-3.53-3.54Zm2.47 1.06a1 1 0 1 0-1.41 1.42 1 1 0 0 0 1.41-1.42Zm5.98-4.17a2.75 2.75 0 0 0-1.81-1.8l-.66-.21c-2.4-.75-5-.1-6.78 1.67l-1 1a3.5 3.5 0 0 0-4.56.32L5.45 6.55c-.29.29-.29.76 0 1.06l1.6 1.59-.18.18c-.69.68-.69 1.79 0 2.47l.5.5-1.4.8a.75.75 0 0 0-.16 1.17l3.89 3.9a.75.75 0 0 0 1.18-.16l.8-1.4.5.5c.68.68 1.78.68 2.47 0l.17-.18 1.6 1.6c.29.28.76.28 1.05 0l1.25-1.25a3.5 3.5 0 0 0 .32-4.57l1-1A6.75 6.75 0 0 0 21.72 5l-.21-.67Zm-2.26-.38c.4.13.7.43.83.83l.2.66c.58 1.86.08 3.9-1.3 5.27l-5.4 5.4c-.1.1-.25.1-.35 0l-5.3-5.3a.25.25 0 0 1 0-.36l5.4-5.4a5.25 5.25 0 0 1 5.26-1.3l.66.2Zm-1.29 9.9a2 2 0 0 1-.3 2.43l-.72.71-1.06-1.06 2.08-2.08ZM7.76 6.36a2 2 0 0 1 2.43-.3L8.1 8.14 7.05 7.08l.7-.72Zm2.82 9.2-.52.9-2.5-2.5.9-.51 2.12 2.11ZM6.69 18.4a.75.75 0 0 0-1.06-1.06l-2.48 2.48a.75.75 0 0 0 1.06 1.06l2.48-2.48Zm-1.94-3c.29.3.29.77 0 1.06l-1.07 1.06a.75.75 0 0 1-1.06-1.06l1.06-1.06c.3-.3.77-.3 1.07 0Zm3.88 4.95a.75.75 0 1 0-1.06-1.06l-1.06 1.06a.75.75 0 0 0 1.06 1.06l1.06-1.06Z'],
    'search': ['M16.1 17.16a8 8 0 1 1 1.06-1.06l4.62 4.62a.75.75 0 1 1-1.06 1.06l-4.62-4.62ZM17.5 11a6.5 6.5 0 1 0-13 0 6.5 6.5 0 0 0 13 0Z'],
    'send': ['M5.7 12 2.3 3.27a.75.75 0 0 1 .94-.98l.1.04 18 9c.51.26.54.97.1 1.28l-.1.06-18 9a.75.75 0 0 1-1.07-.85l.03-.1L5.7 12 2.3 3.27 5.7 12ZM4.4 4.54l2.61 6.7 6.63.01c.38 0 .7.28.74.65v.1c0 .38-.27.7-.64.74l-.1.01H7l-2.6 6.7L19.31 12 4.4 4.54Z'],
    'settings': ['M12.01 2.25c.74 0 1.47.1 2.18.25.32.07.55.33.59.65l.17 1.53a1.38 1.38 0 0 0 1.92 1.11l1.4-.61c.3-.13.64-.06.85.17a9.8 9.8 0 0 1 2.2 3.8c.1.3 0 .63-.26.82l-1.25.92a1.38 1.38 0 0 0 0 2.22l1.25.92c.26.19.36.52.27.82a9.8 9.8 0 0 1-2.2 3.8.75.75 0 0 1-.85.17l-1.4-.62a1.38 1.38 0 0 0-1.93 1.12l-.17 1.52a.75.75 0 0 1-.58.65 9.52 9.52 0 0 1-4.4 0 .75.75 0 0 1-.57-.65l-.17-1.52a1.38 1.38 0 0 0-1.93-1.11l-1.4.62a.75.75 0 0 1-.85-.18 9.8 9.8 0 0 1-2.2-3.8c-.1-.3 0-.63.26-.82l1.25-.92a1.38 1.38 0 0 0 0-2.22l-1.24-.92a.75.75 0 0 1-.28-.82 9.8 9.8 0 0 1 2.2-3.8c.23-.23.57-.3.86-.17l1.4.62c.4.17.86.15 1.25-.08.38-.22.63-.6.68-1.04l.17-1.53a.75.75 0 0 1 .58-.65c.72-.16 1.45-.24 2.2-.25Zm0 1.5c-.45 0-.9.04-1.35.12l-.11.97a2.89 2.89 0 0 1-4.03 2.33l-.9-.4A8.3 8.3 0 0 0 4.29 9.1l.8.59a2.88 2.88 0 0 1 0 4.64l-.8.59a8.3 8.3 0 0 0 1.35 2.32l.9-.4a2.88 2.88 0 0 1 4.02 2.32l.1.99c.9.15 1.8.15 2.7 0l.1-.99a2.88 2.88 0 0 1 4.02-2.32l.9.4a8.3 8.3 0 0 0 1.35-2.32l-.8-.59a2.88 2.88 0 0 1 0-4.64l.8-.59a8.3 8.3 0 0 0-1.35-2.32l-.9.4a2.88 2.88 0 0 1-4.02-2.32l-.1-.98c-.45-.08-.9-.11-1.34-.12ZM12 8.25a3.75 3.75 0 1 1 0 7.5 3.75 3.75 0 0 1 0-7.5Zm0 1.5a2.25 2.25 0 1 0 0 4.5 2.25 2.25 0 0 0 0-4.5Z'],
    'shield': ['M3 5.75c0-.41.34-.75.75-.75 2.66 0 5.26-.94 7.8-2.85.27-.2.63-.2.9 0C14.99 4.05 17.59 5 20.25 5c.41 0 .75.34.75.75V11c0 5-2.96 8.68-8.73 10.95a.75.75 0 0 1-.54 0C5.96 19.68 3 16 3 11V5.75Zm1.5.73V11c0 4.26 2.45 7.38 7.5 9.44 5.05-2.06 7.5-5.18 7.5-9.44V6.48a14.36 14.36 0 0 1-7.5-2.8 14.36 14.36 0 0 1-7.5 2.8Z'],
    'sparkle': ['M8.67 15.73a1.44 1.44 0 0 0 2.16-.61l.61-1.86a2.87 2.87 0 0 1 1.82-1.81l1.78-.58a1.44 1.44 0 0 0-.06-2.74l-1.75-.57a2.88 2.88 0 0 1-1.82-1.82l-.58-1.78a1.45 1.45 0 0 0-2.73.02l-.59 1.8a2.88 2.88 0 0 1-1.77 1.78l-1.77.57a1.44 1.44 0 0 0 .01 2.73l1.76.57a2.89 2.89 0 0 1 1.82 1.83l.58 1.77c.1.29.28.53.53.7Zm-.38-4.25A4.4 4.4 0 0 0 6.21 10l-1.6-.5 1.61-.52A4.4 4.4 0 0 0 8.95 6.2l.52-1.58.51 1.59a4.37 4.37 0 0 0 2.79 2.77l1.61.52-1.58.52a4.38 4.38 0 0 0-2.78 2.77l-.51 1.59-.52-1.59c-.16-.47-.4-.91-.7-1.3Zm8.04 9.3c-.19-.13-.33-.33-.4-.55l-.34-1a1.31 1.31 0 0 0-.82-.83l-.99-.32A1.15 1.15 0 0 1 13 17a1.14 1.14 0 0 1 .77-1.08l1-.33a1.3 1.3 0 0 0 .8-.82l.33-.99a1.14 1.14 0 0 1 2.16-.02l.33 1.01a1.3 1.3 0 0 0 .82.82l.99.32a1.14 1.14 0 0 1 .04 2.17l-1.01.33a1.32 1.32 0 0 0-.82.82l-.32.99a1.14 1.14 0 0 1-1.76.56ZM15.3 17a2.8 2.8 0 0 1 1.7 1.7 2.8 2.8 0 0 1 1.7-1.7 2.81 2.81 0 0 1-1.72-1.7A2.8 2.8 0 0 1 15.3 17Z'],
    'star': ['M10.79 3.1c.5-1 1.92-1 2.42 0l2.36 4.78 5.27.77c1.1.16 1.55 1.52.75 2.3l-3.82 3.72.9 5.25a1.35 1.35 0 0 1-1.96 1.42L12 18.86l-4.72 2.48a1.35 1.35 0 0 1-1.96-1.42l.9-5.25-3.81-3.72c-.8-.78-.36-2.14.75-2.3l5.27-.77 2.36-4.78Zm1.2.94L9.75 8.6c-.2.4-.58.68-1.02.74l-5.05.74 3.66 3.56c.32.3.46.76.39 1.2l-.87 5.02 4.52-2.37c.4-.2.86-.2 1.26 0l4.51 2.37-.86-5.03c-.07-.43.07-.88.39-1.2l3.65-3.55-5.05-.74a1.35 1.35 0 0 1-1.01-.74L12 4.04Z'],
    'target': ['M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm-6-2a6 6 0 1 1 12 0 6 6 0 0 1-12 0Zm6-4.5a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9ZM2 12a10 10 0 1 1 20 0 10 10 0 0 1-20 0Zm10-8.5a8.5 8.5 0 1 0 0 17 8.5 8.5 0 0 0 0-17Z'],
    'timer': ['M12 5a8.5 8.5 0 1 1 0 17 8.5 8.5 0 0 1 0-17Zm0 1.5a7 7 0 1 0 0 14 7 7 0 0 0 0-14ZM12 8c.38 0 .7.28.74.65l.01.1v4.5a.75.75 0 0 1-1.5.1v-4.6c0-.41.34-.75.75-.75Zm7.15-2.89.08.06 1.16.97a.75.75 0 0 1-.88 1.21l-.08-.06-1.16-.96a.75.75 0 0 1 .88-1.22Zm-4.9-2.61a.75.75 0 0 1 .1 1.5h-4.6a.75.75 0 0 1-.1-1.5h4.6Z'],
    'trophy': ['M15.25 2c1.16 0 2.12.88 2.24 2h1.27c.92 0 1.67.7 1.74 1.6v3.15a3.25 3.25 0 0 1-3.06 3.24l-.2.01a5.76 5.76 0 0 1-4.74 3.95v1.55h1.75a3.25 3.25 0 0 1 3.25 3.07V21.25c0 .38-.28.7-.64.74l-.1.01h-10a.75.75 0 0 1-.75-.65v-.6a3.25 3.25 0 0 1 3.06-3.24l.18-.01H11v-1.55A5.76 5.76 0 0 1 6.27 12h-.02A3.25 3.25 0 0 1 3 8.75v-3C3 4.78 3.78 4 4.75 4H6c.13-1.12 1.08-2 2.24-2h7Zm-1 17h-5c-.83 0-1.52.58-1.7 1.35l-.03.15h8.47A1.75 1.75 0 0 0 14.4 19h-.16Zm1-15.5h-7a.75.75 0 0 0-.75.75v6a4.25 4.25 0 0 0 8.5 0v-6a.75.75 0 0 0-.75-.75Zm3.5 2H17.5v4.98c.8-.11 1.43-.76 1.5-1.58V5.75a.25.25 0 0 0-.18-.24l-.06-.01ZM6 5.5H4.75a.25.25 0 0 0-.25.25v3c0 .88.65 1.61 1.5 1.73V5.5Z'],
    'wallet': ['M15.5 13.75c0-.41.34-.75.75-.75h2a.75.75 0 0 1 0 1.5h-2a.75.75 0 0 1-.75-.75ZM3 5h.01c.13-1.12 1.08-2 2.24-2h11.5C17.99 3 19 4 19 5.25v.84a3.25 3.25 0 0 1 2.5 3.16v8.5c0 1.8-1.46 3.25-3.25 3.25h-12A3.25 3.25 0 0 1 3 17.75V5Zm15.25 2.5H4.5v10.25c0 .97.78 1.75 1.75 1.75h12c.97 0 1.75-.78 1.75-1.75v-8.5c0-.97-.78-1.75-1.75-1.75ZM17.5 6v-.75a.75.75 0 0 0-.75-.75H5.25a.75.75 0 0 0 0 1.5H17.5Z'],
    'warning': ['M9.14 3.7a3.25 3.25 0 0 1 5.72 0l6.74 12.5a3.25 3.25 0 0 1-2.86 4.8H5.25a3.25 3.25 0 0 1-2.86-4.8L9.14 3.7Zm4.4.72a1.75 1.75 0 0 0-3.08 0L3.7 16.92a1.75 1.75 0 0 0 1.54 2.58h13.5a1.75 1.75 0 0 0 1.53-2.58l-6.74-12.5ZM12 15a1 1 0 1 1 0 2 1 1 0 0 1 0-2Zm0-7.5c.41 0 .75.34.75.75v4.5a.75.75 0 0 1-1.5 0v-4.5c0-.41.34-.75.75-.75Z'],
    'weather_moon': ['M20.03 17a10 10 0 0 1-16.9.68.75.75 0 0 1 .36-1.13c3.77-1.35 5.79-2.91 6.96-5.15 1.23-2.35 1.55-4.93.69-8.46A.75.75 0 0 1 11.9 2 10 10 0 0 1 20.03 17Zm-8.25-4.9c-1.25 2.39-3.31 4.1-6.82 5.5a8.49 8.49 0 0 0 13.77-1.35 8.5 8.5 0 0 0-5.9-12.63c.64 3.39.22 6.05-1.05 8.48Z'],
};
function F(name, size) {
  const d = (ICONS[name] || []).map(p => `<path d="${p}"/>`).join('');
  return `<svg class="ficon" width="${size || 20}" height="${size || 20}" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">${d}</svg>`;
}
function applyIcons() {
  document.querySelectorAll('[data-f]').forEach(el => {
    el.innerHTML = F(el.dataset.f, el.dataset.fs ? parseInt(el.dataset.fs, 10) : 20);
  });
}

/* API base: same-origin bila disajikan dari server API (Note 8);
   fallback ke Note 8 (LAN) bila UI di-hosting statis (GitHub Pages backup). */
const API_BASE = window.location.hostname.endsWith('github.io')
  ? 'http://192.168.1.5:8443'
  : window.location.origin;

/* ============================================================
   TGQ — Main Application
   Modular, future-proof architecture
   ============================================================ */
const TGQ = (() => {
  // ===== State =====
  let state = {
    markets: [],
    engines: [],
    status: null,
    currentPage: 'home'
  };

  // ===== DOM Cache =====
  const $ = id => document.getElementById(id);
  const dom = {
    navStatus: $('navStatus'),
    statMarkets: $('statMarkets'),
    statEngines: $('statEngines'),
    statStatus: $('statStatus'),
    statVersion: $('statVersion'),
    clockTime: $('clockTime'),
    clockDate: $('clockDate'),
    hokiBox: $('hokiBox'),
    hokiNums: $('hokiNums'),
    hokiMeta: $('hokiMeta'),
    engineSelect: $('engineSelect'),
    marketSelect: $('marketSelect'),
    predBtn: $('predBtn'),
    predResult: $('predResult'),
    predNums: $('predNums'),
    predMeta: $('predMeta'),
    marketSearch: $('marketSearch'),
    marketCount: $('marketCount'),
    marketGrid: $('marketGrid'),
    inputDate: $('inputDate'),
    addMarketSelect: $('addMarketSelect'),
    submitInputBtn: $('submitInputBtn'),
    inputGrid: $('inputGrid'),
    inputCount: $('inputCount'),
    filledCount: $('filledCount'),
    inputStatus: $('inputStatus')
  };

  // ===== Digital Clock (UTC+7 Jakarta) =====
  function startClock() {
    function update() {
      const now = new Date();
      const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
      const jakarta = new Date(utcMs + 7 * 3600000);
      const days = ['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];
      const months = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];
      dom.clockTime.textContent = jakarta.toLocaleTimeString('id-ID', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      dom.clockDate.textContent = `${days[jakarta.getDay()]}, ${jakarta.getDate()} ${months[jakarta.getMonth()]} ${jakarta.getFullYear()}`;
    }
    update();
    setInterval(update, 1000);
  }

  // ===== Navigation =====
  function initNav() {
    document.querySelectorAll('[data-nav], .nav-links a[href^="#"]').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        const href = el.getAttribute('href');
        if (href) showPage(href.replace('#', ''));
      });
    });
    // Hash change
    window.addEventListener('hashchange', () => {
      const page = location.hash.replace('#', '') || 'home';
      showPage(page);
    });
  }

  function showPage(page) {
    if (!page) page = 'home';
    state.currentPage = page;
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
    // Show target
    const target = document.getElementById(page);
    if (target) target.classList.remove('hidden');
    // Update nav
    document.querySelectorAll('.nav-links a').forEach(a => {
      a.classList.toggle('active', a.dataset.page === page);
    });
    // Update hash
    if (location.hash !== '#' + page) {
      history.pushState(null, '', '#' + page);
    }
    // Scroll to top of section
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ===== Load Data =====
  async function loadHoki() {
    try {
      const r = await fetch(API_BASE + '/api/hoki');
      const d = await r.json();
      if (d.success) {
        const main = d.main || [];
        const backup = d.backup || [];
        dom.hokiNums.innerHTML = main.map((n,i) => `<div class="ball" style="animation-delay:${i*0.08}s">${n}</div>`).join('') +
          (backup.length ? `<span class="sep">cad:</span>` +
            backup.map((n,i) => `<div class="ball bu" style="animation-delay:${(main.length+i)*0.08}s">${n}</div>`).join('') : '');
        dom.hokiMeta.innerHTML = `${F('sparkle',13)} ${d.generated_at} · ${F('data_bar_vertical',13)} ${d.stats.total_records_analyzed} data dianalisis dari ${d.stats.markets_analyzed} pasar`;
      } else {
        dom.hokiNums.innerHTML = '<span style="color:var(--text-muted);font-size:13px">Tidak tersedia</span>';
      }
    } catch(e) {
      dom.hokiNums.innerHTML = '<span style="color:var(--text-muted);font-size:13px">Gagal memuat</span>';
    }
  }

  async function loadStatus() {
    try {
      const r = await fetch(API_BASE + '/api/status');
      state.status = await r.json();
      dom.statMarkets.textContent = state.status.market_count || '—';
      dom.statEngines.textContent = state.status.engine_count || '—';
      dom.statStatus.textContent = state.status.status || '—';
      dom.statVersion.textContent = 'v' + (state.status.version || '—');
      dom.navStatus.textContent = state.status.status === 'ready' ? 'Online' : 'Offline';
    } catch(e) {
      dom.navStatus.textContent = 'Error';
    }
  }

  async function loadEngines() {
    try {
      const r = await fetch(API_BASE + '/api/engines');
      const d = await r.json();
      state.engines = d.engines || [];
      dom.engineSelect.innerHTML = state.engines.map(e =>
        `<option value="${e}">${e.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase())}</option>`
      ).join('');
    } catch(e) {
      dom.engineSelect.innerHTML = '<option value="">Gagal load engine</option>';
    }
  }

  async function loadMarkets() {
    try {
      const r = await fetch(API_BASE + '/api/markets');
      const d = await r.json();
      state.markets = d.markets || [];
      dom.marketCount.textContent = state.markets.length;
      renderMarkets(state.markets);
      // Populate market select
      dom.marketSelect.innerHTML = state.markets.map(m =>
        `<option value="${m.name}">${m.name}</option>`
      ).join('');
      // Update input market select
      allMarkets = state.markets;
      updateAddMarketSelect();
    } catch(e) {
      dom.marketGrid.innerHTML = '<div style="color:#e74c3c">Gagal memuat data pasar</div>';
    }
  }

  // ===== Market Rendering =====
  function renderMarkets(list) {
    dom.marketGrid.innerHTML = list.map(m =>
      `<div class="market-item">
        <div><div class="name">${m.name}</div><div class="period">Periode ${m.latest_period}</div></div>
        <div class="result">${m.latest_result}</div>
      </div>`
    ).join('');
  }

  function filterMarkets() {
    const q = dom.marketSearch.value.toUpperCase();
    const filtered = state.markets.filter(m => m.name.includes(q));
    dom.marketCount.textContent = filtered.length;
    renderMarkets(filtered);
  }

  // ===== Prediction =====
  async function predict() {
    const engine = dom.engineSelect.value;
    const market = dom.marketSelect.value;
    if (!engine || !market) {
      dom.predNums.innerHTML = '<div style="color:#e74c3c">Pilih engine dan market terlebih dahulu</div>';
      dom.predResult.classList.add('show');
      return;
    }
    dom.predBtn.disabled = true;
    dom.predBtn.innerHTML = '<span class="spinner"></span> Memproses...';
    dom.predResult.classList.remove('show');
    try {
      const r = await fetch(API_BASE + '/api/predict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({engine, market})
      });
      const d = await r.json();
      if (d.success) {
        const nums = d.prediction.main || [];
        const backup = d.prediction.backup || [];
        dom.predNums.innerHTML = nums.map((n,i) => `<div class="ball" style="animation-delay:${i*0.08}s">${n}</div>`).join('') +
          (backup.length ? '<span style="color:var(--text-muted);font-size:13px;margin:0 4px">cad:</span>' +
            backup.map((n,i) => `<div class="ball backup" style="animation-delay:${(nums.length+i)*0.08}s">${n}</div>`).join('') : '');
        dom.predMeta.innerHTML =
          `<span>${F('target',13)} Periode ${d.target_period}</span>` +
          `<span>${F('chart_person',13)} ${(d.confidence * 100).toFixed(0)}%</span>` +
          `<span>${F('settings',13)} ${d.method || '—'}</span>` +
          `<span>${F('timer',13)} ${d.timestamp}</span>`;
        dom.predResult.classList.add('show');
      } else {
        dom.predNums.innerHTML = `<div style="color:#e74c3c">${d.detail || 'Prediksi gagal'}</div>`;
        dom.predResult.classList.add('show');
      }
    } catch(e) {
      dom.predNums.innerHTML = `<div style="color:#e74c3c">Error: ${e.message}</div>`;
      dom.predResult.classList.add('show');
    }
    dom.predBtn.disabled = false;
    dom.predBtn.innerHTML = F('sparkle',16) + ' Prediksi';
  }

  // ===== Input Data =====
  let inputRows = [];
  let allMarkets = [];

  function initInput() {
    // Set default date to today (Jakarta UTC+7)
    const now = new Date();
    const utcMs = now.getTime() + now.getTimezoneOffset() * 60000;
    const jakarta = new Date(utcMs + 7 * 3600000);
    dom.inputDate.value = jakarta.toISOString().split('T')[0];

    // Populate add-market dropdown
    allMarkets = state.markets.length ? state.markets : [];
    updateAddMarketSelect();

    // Single change handler for add-market select
    dom.addMarketSelect.addEventListener('change', function() {
      const val = this.value;
      if (!val) return;
      if (val === '__all__') {
        const added = new Set(inputRows.map(r => r.name));
        const available = allMarkets.filter(m => !added.has(m.name || m));
        available.forEach(m => {
          const name = m.name || m;
          if (!added.has(name)) addInputRow(name);
        });
      } else if (val === '__custom__') {
        const custom = prompt('Nama pasar custom:');
        if (custom && custom.trim()) addInputRow(custom.trim());
      } else {
        addInputRow(val);
      }
      this.value = '';
    });

    // Load saved input rows if any
    loadSavedInput();
  }

  function updateAddMarketSelect() {
    const added = new Set(inputRows.map(r => r.name));
    const available = allMarkets.filter(m => !added.has(m.name || m));
    const html = '<option value="">+ Tambah pasar...</option>' +
      '<option value="__all__">+ Tambah semua pasar</option>' +
      available.map(m => {
        const name = m.name || m;
        return `<option value="${name}">${name}</option>`;
      }).join('') +
      '<option value="__custom__">+ Custom market...</option>';
    dom.addMarketSelect.innerHTML = html;
  }

  function addInputRow(marketName) {
    if (inputRows.some(r => r.name === marketName)) return;
    const row = { name: marketName, result: '', period: '' };
    inputRows.push(row);

    const div = document.createElement('div');
    div.className = 'input-box';
    div.dataset.market = marketName;
    div.innerHTML =
      `<div class="header">
        <span class="market-name">${marketName}</span>
        <button class="remove-btn" onclick="TGQ.removeInputRow('${marketName}')" title="Hapus">${F('dismiss',16)}</button>
      </div>
      <div class="input-fields">
        <div class="field">
          <label>Result</label>
          <input type="text" id="inp_${marketName}_result" placeholder="cth: 1234" oninput="TGQ.updateInputSummary()">
        </div>
        <div class="field">
          <label>Periode</label>
          <input type="text" id="inp_${marketName}_period" placeholder="cth: 2026-07-29" oninput="TGQ.updateInputSummary()">
        </div>
      </div>`;
    dom.inputGrid.appendChild(div);
    updateAddMarketSelect();
    updateInputSummary();
    saveInputRows();
  }

  function removeInputRow(marketName) {
    inputRows = inputRows.filter(r => r.name !== marketName);
    const el = dom.inputGrid.querySelector(`[data-market="${marketName}"]`);
    if (el) el.remove();
    updateAddMarketSelect();
    updateInputSummary();
    saveInputRows();
  }

  // ── Orphan market slot config (sama seperti config/orphan_markets.json) ──
  const ORPHAN_SLOTS = [
    { after: 'KING KONG 4D POOL', idx: 0, market: 'HOKIdraw' },
    { after: 'KING KONG 4D POOL', idx: 1, market: 'huahin0100' },
    { after: 'KENTUCKYEVE POOL', idx: 0, market: 'cambodialotto' },
    { after: 'BULLSEYE POOL', idx: 0, market: 'poipet12' },
    { after: 'OREGON12 POOL', idx: 0, market: 'sydneylotto' },
    { after: 'CHELSEA 15 POOL', idx: 0, market: 'poipet15' },
    { after: 'CHELSEA 15 POOL', idx: 1, market: 'totomali1530' },
    { after: 'CHELSEA 15 POOL', idx: 2, market: 'huahin1630' },
    { after: 'CHELSEA 19 POOL', idx: 0, market: 'poipet19' },
    { after: 'PCSO POOL', idx: 0, market: 'totomali2030' },
    { after: 'PCSO POOL', idx: 1, market: 'huahin2100' },
    { after: 'BRUNEI 21 POOL', idx: 0, market: 'poipet22' },
    { after: 'BRUNEI 21 POOL', idx: 1, market: 'hongkonglotto' },
    { after: 'BRUNEI 21 POOL', idx: 2, market: 'totomali2330' }
  ];

  function _fillInputRow(marketName, result, period) {
    const existing = inputRows.find(r => r.name.toUpperCase() === marketName.toUpperCase());
    if (existing) {
      if (result) existing.result = result;
      if (period) existing.period = period;
      const ri = document.getElementById(`inp_${existing.name}_result`);
      const pi = document.getElementById(`inp_${existing.name}_period`);
      if (ri) ri.value = result;
      if (pi) pi.value = period;
    } else {
      const found = allMarkets.find(m => {
        const mn = (m.name || m).toUpperCase().replace(/\s+/g, '');
        return mn === marketName;
      });
      const finalName = found ? (found.name || found) : marketName;
      addInputRow(finalName);
      const row = inputRows.find(r => r.name === finalName);
      if (row) {
        if (result) row.result = result;
        if (period) row.period = period;
        const ri = document.getElementById(`inp_${finalName}_result`);
        const pi = document.getElementById(`inp_${finalName}_period`);
        if (ri) ri.value = result;
        if (pi) pi.value = period;
      }
    }
  }

  // ===== Luna Parse (password protected) =====
  const LUNA_PASSWORD = '292511';

  function showLunaModal() {
    document.getElementById('lunaModal').style.display = 'flex';
    document.getElementById('lunaPassword').value = '';
    document.getElementById('lunaPasswordError').style.display = 'none';
    setTimeout(() => document.getElementById('lunaPassword').focus(), 100);
  }

  function closeLunaModal() {
    document.getElementById('lunaModal').style.display = 'none';
  }

  function renderLunaResults(results) {
    const grid = document.getElementById('lunaResultsGrid');
    const summary = document.getElementById('lunaResultsSummary');
    const panel = document.getElementById('lunaResults');

    if (!results || results.length === 0) {
      panel.style.display = 'none';
      return;
    }

    grid.innerHTML = results.map(r =>
      '<div class="lr-item">' +
        '<span class="lr-market">' + r.market + '</span>' +
        '<span class="lr-result">' + r.result + '</span>' +
        '<span class="lr-period">#' + (r.period || '\u2014') + '</span>' +
      '</div>'
    ).join('');

    const filled = results.filter(r => r.result && r.period).length;
    summary.innerHTML =
      '<span>' + F('box',14) + ' <strong>' + results.length + '</strong> pasar diekstrak</span>' +
      '<span>' + F('checkmark',14) + ' <strong>' + filled + '</strong> siap kirim</span>' +
      '<span>' + F('send',14) + ' <strong>' + filled + '</strong> data dikirim</span>';

    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  async function lunaParse() {
    const password = document.getElementById('lunaPassword').value;
    if (password !== LUNA_PASSWORD) {
      document.getElementById('lunaPasswordError').style.display = 'block';
      document.getElementById('lunaPassword').focus();
      return;
    }
    closeLunaModal();

    // Jalankan parse seperti biasa
    const textarea = document.getElementById('lunaPaste');
    let text = textarea.value;
    if (!text.trim()) {
      dom.inputStatus.className = 'error';
      dom.inputStatus.innerHTML = F('warning',14) + ' Tidak ada data di Luna paste!';
      return;
    }

    dom.inputStatus.className = 'sending';
    dom.inputStatus.innerHTML = F('key',14) + ' Luna Parse: Mengekstrak data...';

    // Parse data (reuse parsePaste logic)
    const uiArtifacts = ['Play Now', 'btn_live', 'labelthumbnail', 'thumbnail', 'label'];
    const rawLines = text.split('\n');
    const strippedLines = rawLines.map(l => l.trim());

    // Sanitasi
    const sanitized = rawLines.map((l, i) => {
      const s = l.trim();
      if (!s) return '';
      if (uiArtifacts.includes(s) || uiArtifacts.some(a => s.includes(a))) return null;
      return l;
    }).filter(l => l !== null).join('\n');

    const blocks = sanitized.split(/\n{2,}/).filter(b => b.trim());
    const extracted = [];

    blocks.forEach(block => {
      const blockLines = block.split('\n').map(l => l.trim()).filter(l => l);
      if (blockLines.length < 2) return;

      const poolIdx = blockLines.findIndex(l => /POOL/i.test(l));
      if (poolIdx === -1) return;

      let marketName = blockLines[poolIdx].split(/POOL/i)[0].trim().toUpperCase().replace(/\s+/g, '');
      if (!marketName) return;

      let result = '';
      for (let j = poolIdx + 1; j < Math.min(poolIdx + 5, blockLines.length); j++) {
        const digitLine = blockLines[j].replace(/[^0-9]/g, '');
        if (digitLine && (digitLine.length === 4 || digitLine.length === 5)) {
          result = digitLine;
          break;
        }
      }

      let period = '';
      for (let j = poolIdx + 1; j < Math.min(poolIdx + 5, blockLines.length); j++) {
        const m = blockLines[j].match(/PERIODE\s*:\s*(\d+)/i);
        if (m) {
          period = m[1];
          break;
        }
      }

      if (!result) return;

      const aliasMap = {
        'TOTOMACAU': '4DTOTOMACAU', 'TOTOMACAO': '4DTOTOMACAU',
        'TOTOMACAU4D': '4DTOTOMACAU', '4DTOTOMACAU': '4DTOTOMACAU',
        'TOTOMACAU5D': '5DTOTOMACAU', '5DTOTOMACAU': '5DTOTOMACAU',
        'TOTOMACAU6D': '6DTOTOMACAU', '6DTOTOMACAU': '6DTOTOMACAU',
        'KINGKONG4D': 'KINGKONG4D',
      };
      marketName = aliasMap[marketName] || marketName;

      extracted.push({ market: marketName, result: result, period: period });
    });

    // Orphan detection
    const orphanResults = {};
    for (let i = 0; i < strippedLines.length; i++) {
      const line = strippedLines[i];
      if (!line || uiArtifacts.includes(line) || uiArtifacts.some(a => line.includes(a))) continue;

      if (/POOL/i.test(line)) {
        const marketHeader = line;
        let j = i + 1;
        let skipped = 0;
        while (j < strippedLines.length && skipped < 3) {
          const l = strippedLines[j];
          if (l && /^\d{4,5}$/.test(l)) { skipped++; }
          else if (l && /^\[?PERIODE/i.test(l)) { skipped++; }
          else if (l === 'Play Now') { skipped++; }
          j++;
        }

        const orphans = [];
        let k = j;
        while (k < strippedLines.length) {
          const l = strippedLines[k];
          if (/POOL/i.test(l) && !uiArtifacts.includes(l)) break;

          if (k + 2 < strippedLines.length
              && strippedLines[k] === ''
              && /^\d{4,5}$/.test(strippedLines[k+1])
              && strippedLines[k+2] === '') {
            orphans.push(strippedLines[k+1]);
            k += 3;
            continue;
          }

          if (k + 2 < strippedLines.length
              && /^\d{4,5}$/.test(strippedLines[k])
              && strippedLines[k+1].includes(':')
              && strippedLines[k+2] === 'btn_live') {
            orphans.push(strippedLines[k]);
            k += 3;
            continue;
          }

          k++;
        }

        if (orphans.length > 0) {
          orphanResults[marketHeader] = orphans;
        }
      }
    }

    const ORPHAN_SLOTS = [
      { after: 'KING KONG 4D POOL', idx: 0, market: 'HOKIDRAW' },
      { after: 'KING KONG 4D POOL', idx: 1, market: 'HUAHIN0100' },
      { after: 'KENTUCKYEVE POOL', idx: 0, market: 'CAMBODIALOTTO' },
      { after: 'BULLSEYE POOL', idx: 0, market: 'POIPET12' },
      { after: 'OREGON12 POOL', idx: 0, market: 'SYDNEYLOTTO' },
      { after: 'CHELSEA 15 POOL', idx: 0, market: 'POIPET15' },
      { after: 'CHELSEA 15 POOL', idx: 1, market: 'TOTOMALI1530' },
      { after: 'CHELSEA 15 POOL', idx: 2, market: 'HUAHIN1630' },
      { after: 'CHELSEA 19 POOL', idx: 0, market: 'POIPET19' },
      { after: 'PCSO POOL', idx: 0, market: 'TOTOMALI2030' },
      { after: 'PCSO POOL', idx: 1, market: 'HUAHIN2100' },
      { after: 'BRUNEI 21 POOL', idx: 0, market: 'POIPET22' },
      { after: 'BRUNEI 21 POOL', idx: 1, market: 'HONGKONGLOTTO' },
      { after: 'BRUNEI 21 POOL', idx: 2, market: 'TOTOMALI2330' },
    ];

    ORPHAN_SLOTS.forEach(slot => {
      const afterHeader = slot.after;
      const orphans = orphanResults[afterHeader];
      if (orphans && slot.idx < orphans.length) {
        extracted.push({ market: slot.market, result: orphans[slot.idx], period: '' });
      }
    });

    if (extracted.length === 0) {
      dom.inputStatus.className = 'error';
      dom.inputStatus.innerHTML = F('warning',14) + ' Tidak ada data valid yang ditemukan!';
      return;
    }

    // Tampilkan hasil ekstraksi
    renderLunaResults(extracted);

    // Route ke input grid
    extracted.forEach(item => {
      _fillInputRow(item.market, item.result, item.period);
    });

    updateInputSummary();
    saveInputRows();

    dom.inputStatus.className = 'sending';
    dom.inputStatus.innerHTML = F('arrow_upload',14) + ' Luna Parse: ' + extracted.length + ' data diekstrak, mengirim...';

    // Auto-submit ke API
    const date = dom.inputDate.value;
    if (!date) {
      dom.inputStatus.className = 'error';
      dom.inputStatus.innerHTML = F('warning',14) + ' Pilih tanggal terlebih dahulu!';
      return;
    }

    const allPayload = extracted.map(r => ({
      market: r.market,
      result: r.result,
      period: r.period || '0',
      date: date
    }));

    try {
      const apiBase = window.location.origin;
      const r = await fetch(apiBase + '/api/input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: date, items: allPayload })
      });
      const result = await r.json();

      if (result.success) {
        dom.inputStatus.className = 'success';
        dom.inputStatus.innerHTML = F('checkmark_circle',14) + ' Luna Parse: ' + result.saved + ' data tersimpan!';
      } else {
        dom.inputStatus.className = 'error';
        dom.inputStatus.innerHTML = F('error_circle',14) + ' Gagal: ' + (result.message || 'Unknown error');
      }
    } catch(e) {
      dom.inputStatus.className = 'error';
      dom.inputStatus.innerHTML = F('error_circle',14) + ' Error: ' + e.message;
    }

    // Flash hijau pada textarea
    textarea.style.borderColor = '#10b981';
    setTimeout(() => { textarea.style.borderColor = ''; }, 2000);
  }

  function parsePaste() {
    const textarea = document.getElementById('lunaPaste');
    let text = textarea.value;
    if (!text.trim()) return;

    const uiArtifacts = ['Play Now', 'btn_live', 'labelthumbnail', 'thumbnail'];
    const rawLines = text.split('\n');
    const strippedLines = rawLines.map(l => l.trim());

    // ── TAHAP 1: Parse named markets (dengan POOL) ──
    // Sanitasi — buang UI artifacts, pertahankan blank lines
    const sanitized = rawLines.map((l, i) => {
      const s = l.trim();
      if (!s) return '';                         // blank line tetap sebagai separator
      if (uiArtifacts.includes(s) || uiArtifacts.some(a => s.includes(a))) return null;
      return l;
    }).filter(l => l !== null).join('\n');

    const blocks = sanitized.split(/\n{2,}/).filter(b => b.trim());
    let addedCount = 0;

    blocks.forEach(block => {
      const blockLines = block.split('\n').map(l => l.trim()).filter(l => l);
      if (blockLines.length < 2) return;

      const poolIdx = blockLines.findIndex(l => /POOL/i.test(l));
      if (poolIdx === -1) return;

      let marketName = blockLines[poolIdx].split(/POOL/i)[0].trim().toUpperCase().replace(/\s+/g, '');
      if (!marketName) return;

      let result = '';
      for (let j = poolIdx + 1; j < Math.min(poolIdx + 5, blockLines.length); j++) {
        const digitLine = blockLines[j].replace(/[^0-9]/g, '');
        if (digitLine && (digitLine.length === 4 || digitLine.length === 5)) {
          result = digitLine;
          break;
        }
      }

      let period = '';
      for (let j = poolIdx + 1; j < Math.min(poolIdx + 5, blockLines.length); j++) {
        const m = blockLines[j].match(/PERIODE\s*:\s*(\d+)/i);
        if (m) {
          period = m[1];
          break;
        }
      }

      if (!result) return;

      // Normalisasi alias
      const aliasMap = {
        'TOTOMACAU': '4DTOTOMACAU', 'TOTOMACAO': '4DTOTOMACAU',
        'TOTOMACAU4D': '4DTOTOMACAU', '4DTOTOMACAU': '4DTOTOMACAU',
        'TOTOMACAU5D': '5DTOTOMACAU', '5DTOTOMACAU': '5DTOTOMACAU',
        'TOTOMACAU6D': '6DTOTOMACAU', '6DTOTOMACAU': '6DTOTOMACAU',
        'KINGKONG4D': 'KINGKONG4D',
      };
      marketName = aliasMap[marketName] || marketName;

      _fillInputRow(marketName, result, period);
      addedCount++;
    });

    // ── TAHAP 2: Parse orphan markets (position-based, seperti market_sync.py) ──
    // Iterasi line-by-line, cari POOL markets, lalu collect orphan digits setelahnya
    const orphanResults = {}; // afterMarket_header → [digit, digit, ...]

    for (let i = 0; i < strippedLines.length; i++) {
      const line = strippedLines[i];
      if (!line || uiArtifacts.includes(line) || uiArtifacts.some(a => line.includes(a))) continue;

      // Deteksi named POOL market
      if (/POOL/i.test(line)) {
        const marketHeader = line; // simpan header asli (dengan spasi)

        // Skip: result, [PERIODE], Play Now
        let j = i + 1;
        let skipped = 0;
        while (j < strippedLines.length && skipped < 3) {
          const l = strippedLines[j];
          if (l && /^\d{4,5}$/.test(l)) { skipped++; }
          else if (l && /^\[?PERIODE/i.test(l)) { skipped++; }
          else if (l === 'Play Now') { skipped++; }
          else if (!l) { /* blank line — tetap lanjut */ }
          j++;
        }

        // Collect consecutive orphan digits setelah market ini
        const orphans = [];
        let k = j;
        while (k < strippedLines.length) {
          const l = strippedLines[k];

          // Berhenti jika ketemu POOL market berikutnya
          if (/POOL/i.test(l) && !uiArtifacts.includes(l)) break;

          // Pattern A: blank → DIGIT → blank (labelthumbnail type)
          if (k + 2 < strippedLines.length
              && strippedLines[k] === ''
              && /^\d{4,5}$/.test(strippedLines[k+1])
              && strippedLines[k+2] === '') {
            orphans.push(strippedLines[k+1]);
            k += 3;
            continue;
          }

          // Pattern B: DIGIT → TIME (mm:ss) → btn_live (thumbnail type)
          if (k + 2 < strippedLines.length
              && /^\d{4,5}$/.test(strippedLines[k])
              && strippedLines[k+1].includes(':')
              && strippedLines[k+2] === 'btn_live') {
            orphans.push(strippedLines[k]);
            k += 3;
            continue;
          }

          k++;
        }

        if (orphans.length > 0) {
          orphanResults[marketHeader] = orphans;
        }
      }
    }

    // Map orphan results ke market names via slot config
    ORPHAN_SLOTS.forEach(slot => {
      const afterHeader = slot.after;
      const orphans = orphanResults[afterHeader];
      if (orphans && slot.idx < orphans.length) {
        const result = orphans[slot.idx];
        _fillInputRow(slot.market.toUpperCase(), result, '');
        addedCount++;
      }
    });

    updateInputSummary();
    saveInputRows();

    // Flash + toast
    textarea.style.borderColor = '#2ecc71';
    setTimeout(() => { textarea.style.borderColor = ''; }, 1500);

    if (addedCount > 0) {
      showParseToast(addedCount);
      setTimeout(() => TGQ.submitInput(), 300);
    }
  }

  function showParseToast(count) {
    const existing = document.getElementById('parseToast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'parseToast';
    toast.style.cssText = `
      position:fixed;bottom:24px;right:24px;z-index:9999;
      background:var(--bg-card);border:1px solid #2ecc71;border-radius:var(--radius-md);
      padding:16px 24px;box-shadow:0 8px 32px rgba(0,0,0,.4);
      animation:popIn .25s ease;max-width:360px;
    `;
    toast.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px">
        ${F('checkmark_circle',24)}
        <div>
          <div style="font-weight:600;font-size:14px;color:#2ecc71">${count} Market Terkirim!</div>
          <div style="font-size:12px;color:var(--text-secondary);margin-top:2px">Data langsung diproses ke server</div>
        </div>
        <button onclick="this.closest('#parseToast').remove()" style="
          background:none;border:none;color:var(--text-muted);cursor:pointer;padding:0 0 0 8px;display:inline-flex;align-items:center
        ">${F('dismiss',18)}</button>
      </div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => { const t = document.getElementById('parseToast'); if (t) t.remove(); }, 5000);
  }

  function updateInputSummary() {
    let filled = 0;
    inputRows.forEach(r => {
      const res = document.getElementById(`inp_${r.name}_result`);
      const per = document.getElementById(`inp_${r.name}_period`);
      if (res) r.result = res.value;
      if (per) r.period = per.value;
      if (r.result && r.period) filled++;
    });
    dom.inputCount.textContent = inputRows.length;
    dom.filledCount.textContent = filled;
    dom.submitInputBtn.disabled = filled === 0;
  }

  function saveInputRows() {
    try {
      // Save full data including filled values
      const data = inputRows.map(r => ({
        name: r.name,
        result: document.getElementById(`inp_${r.name}_result`)?.value || r.result || '',
        period: document.getElementById(`inp_${r.name}_period`)?.value || r.period || ''
      }));
      localStorage.setItem('tgq_input_data', JSON.stringify(data));
      // Also save textarea content
      const ta = document.getElementById('lunaPaste');
      if (ta) localStorage.setItem('tgq_paste_text', ta.value);
    } catch(e) {}
  }

  function loadSavedInput() {
    try {
      // Restore textarea content
      const ta = document.getElementById('lunaPaste');
      const savedText = localStorage.getItem('tgq_paste_text');
      if (ta && savedText) ta.value = savedText;

      // Restore full input data with values
      const saved = localStorage.getItem('tgq_input_data');
      if (saved) {
        const data = JSON.parse(saved);
        data.forEach(item => {
          // Add row if not already present
          if (!inputRows.some(r => r.name === item.name)) {
            addInputRow(item.name);
          }
          // Fill values
          const row = inputRows.find(r => r.name === item.name);
          if (row) {
            if (item.result) row.result = item.result;
            if (item.period) row.period = item.period;
            const resInp = document.getElementById(`inp_${item.name}_result`);
            const perInp = document.getElementById(`inp_${item.name}_period`);
            if (resInp) resInp.value = item.result || '';
            if (perInp) perInp.value = item.period || '';
          }
        });
        updateInputSummary();
      }
    } catch(e) {}
  }

  async function submitInput() {
    updateInputSummary();
    const date = dom.inputDate.value;
    if (!date) {
      dom.inputStatus.className = 'error';
      dom.inputStatus.innerHTML = F('warning',14) + ' Pilih tanggal terlebih dahulu';
      return;
    }

    // Gather filled rows
    const payload = [];
    inputRows.forEach(r => {
      if (r.result && r.period) {
        payload.push({ market: r.name, result: r.result, period: r.period, date });
      }
    });

    if (payload.length === 0) {
      dom.inputStatus.className = 'error';
      dom.inputStatus.innerHTML = F('warning',14) + ' Tidak ada data yang siap dikirim. Isi result & periode minimal 1 pasar.';
      return;
    }

    dom.inputStatus.className = 'sending';
    dom.inputStatus.innerHTML = F('send',14) + ` Mengirim ${payload.length} data...`;
    dom.submitInputBtn.disabled = true;

    try {
      // Send all data to /api/input
      // - On Note 8: writes langsung ke data_harian/
      // - On read-only FS: fallback commit ke GitHub repo via API
      const r = await fetch(API_BASE + '/api/input', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, items: payload })
      });
      const result = await r.json();

      if (result.success) {
        dom.inputStatus.className = 'success';
        dom.inputStatus.innerHTML = F('checkmark_circle',14) + ` ${result.saved} data berhasil dikirim!`;
        // Clear filled fields
        inputRows.forEach(r => {
          const res = document.getElementById(`inp_${r.name}_result`);
          const per = document.getElementById(`inp_${r.name}_period`);
          if (res) res.value = '';
          if (per) per.value = '';
          r.result = '';
          r.period = '';
        });
        updateInputSummary();
      } else {
        dom.inputStatus.className = 'error';
        dom.inputStatus.innerHTML = F('error_circle',14) + ` Gagal: ${result.message || 'Unknown error'}`;
        if (result.errors && result.errors.length) {
          dom.inputStatus.innerHTML += '<br><small>' + result.errors.slice(0,3).join('<br>') + '</small>';
        }
      }
    } catch(e) {
      dom.inputStatus.className = 'error';
      dom.inputStatus.innerHTML = F('error_circle',14) + ` Error: ${e.message}`;
    }
    dom.submitInputBtn.disabled = false;
  }

  function clearInput() {
    // Clear all market rows
    inputRows.forEach(r => {
      const res = document.getElementById(`inp_${r.name}_result`);
      const per = document.getElementById(`inp_${r.name}_period`);
      if (res) res.value = '';
      if (per) per.value = '';
      r.result = '';
      r.period = '';
    });
    // Also clear paste textarea
    const ta = document.getElementById('lunaPaste');
    if (ta) ta.value = '';
    updateInputSummary();
    dom.inputStatus.className = '';
    dom.inputStatus.textContent = '';
    // Clear saved
    try { localStorage.removeItem('tgq_input_rows'); } catch(e) {}
    // Remove all rows
    inputRows.slice().forEach(r => removeInputRow(r.name));
    inputRows = [];
    dom.inputGrid.innerHTML = '';
    updateAddMarketSelect();
    updateInputSummary();
  }

  // ===== Init =====
  function init() {
    applyIcons();
    startClock();
    initNav();
    loadStatus();
    loadHoki();
    loadEngines();
    loadMarkets();
    initInput();
    // Show initial page from hash
    const page = location.hash.replace('#', '') || 'home';
    showPage(page);
  }

  // Public API
  return { init, predict, filterMarkets, startClock, showPage, addInputRow, removeInputRow, submitInput, clearInput, updateInputSummary, parsePaste, lunaParse, showLunaModal, closeLunaModal, renderLunaResults };
})();

// Start
document.addEventListener('DOMContentLoaded', TGQ.init);
</script>
</body>
</html>"""

@app.get('/')
def home():
    return HTMLResponse(LANDING_HTML)

@app.get('/api/status')
def api_status():
    try:
        executor = Executor()
        engines = executor.get_available_engines()
    except Exception:
        engines = []
    return {
        'app': 'TGQ',
        'version': '1.0',
        'status': 'ready',
        'timezone': 'Asia/Jakarta',
        'engines': engines,
        'engine_count': len(engines),
        'markets': MARKET_LIST,
        'market_count': len(MARKET_LIST),
    }

@app.post('/api/input')
def api_input(data: dict):
    """Receive input data from the TGQ UI.

    Data disimpan dalam format file harian DD-MM-YYYY-Luna.md.
    - Pada Note 8: ditulis langsung ke data_harian/
    - Pada filesystem read-only: di-commit ke GitHub repo (backup) via API
    
    Format entry:
        MARKET NAME POOL
        XXXX
        [PERIODE : NNNNN]
    """
    date = data.get('date')  # Format: YYYY-MM-DD
    items = data.get('items', [])
    if not date or not items:
        raise HTTPException(status_code=400, detail='date and items required')
    
    # Konversi tanggal ke DD-MM-YYYY untuk nama file
    try:
        dt = datetime.strptime(date, '%Y-%m-%d')
        file_date = dt.strftime('%d-%m-%Y')
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid date format, use YYYY-MM-DD')
    
    filename = f'{file_date}-Luna.md'
    saved = 0
    errors = []
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data_harian')
    
    # Format data entries
    new_entries = []
    for item in items:
        market = item.get('market', '').strip().upper()
        result = item.get('result', '').strip()
        period = item.get('period', '').strip()
        if not market or not result:
            errors.append(f'{market or "?"}: missing result')
            continue
        # Format: MARKET NAME POOL\nXXXX\n[PERIODE : NNNNN]\n
        entry = f'\n{market} POOL\n{result}\n[PERIODE : {period}]\n'
        new_entries.append((market, entry))
    
    if not new_entries:
        return {'success': False, 'saved': 0, 'message': 'Tidak ada data valid'}
    
    # 1) Coba tulis lokal (berhasil di Note 8 / local)
    file_path = os.path.join(data_dir, filename)
    try:
        os.makedirs(data_dir, exist_ok=True)
        with open(file_path, 'a') as f:
            for _, entry in new_entries:
                f.write(entry)
                saved += 1
        # Rebuild pasaran_luna/index.json segera supaya halaman pasar
        # menampilkan data terbaru tanpa menunggu pemicu prediksi/sync lain.
        try:
            sync = MarketSync(project_root=str(os.path.join(os.path.dirname(__file__), '..')))
            sync.sync_all()
        except OSError:
            pass  # Read-only filesystem — abaikan, index akan tersync oleh pemicu lain
        return {'success': True, 'saved': saved, 'errors': errors if errors else None,
                'message': f'{saved} data tersimpan ke {filename}'}
    except OSError:
        pass  # Read-only — lanjut ke GitHub API
    
    # 2) Read-only filesystem — commit ke GitHub (22112020.github.io) via API
    import urllib.request, urllib.error
    import base64
    
    github_token = _get_github_token()
    if not github_token:
        return {'success': False, 'saved': 0,
                'message': 'GitHub token tidak ditemukan. Set GITHUB_TOKEN env.'}
    
    repo = '22112020/22112020.github.io'
    branch = 'master'
    api_base = f'https://api.github.com/repos/{repo}/contents'
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'TGQ-App/1.0',
    }
    
    path = f'data_harian/{filename}'
    
    try:
        # GET file dulu untuk dapat SHA (jika sudah ada)
        req_get = urllib.request.Request(f'{api_base}/{path}?ref={branch}',
                                          headers=headers, method='GET')
        sha = None
        existing_content = ''
        try:
            with urllib.request.urlopen(req_get, timeout=10) as resp:
                existing = json.loads(resp.read())
                sha = existing.get('sha')
                if existing.get('content'):
                    existing_content = base64.b64decode(existing['content']).decode('utf-8')
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        
        # Append semua entry baru
        all_entries = ''.join(entry for _, entry in new_entries)
        new_content = existing_content + all_entries if existing_content else all_entries
        content_b64 = base64.b64encode(new_content.encode()).decode()
        
        payload = {
            'message': f'input: {saved} data ke {filename}',
            'content': content_b64,
            'branch': branch,
        }
        if sha:
            payload['sha'] = sha
        
        req_put = urllib.request.Request(f'{api_base}/{path}',
                                          data=json.dumps(payload).encode(),
                                          headers=headers, method='PUT')
        with urllib.request.urlopen(req_put, timeout=15) as resp:
            saved = len(new_entries)
    except Exception as e:
        errors.append(str(e))
    
    return {
        'success': saved > 0,
        'saved': saved,
        'errors': errors if errors else None,
        'message': f'{saved} data di-commit ke GitHub ({filename})' + (f', {len(errors)} gagal' if errors else ''),
    }


def _get_github_token() -> str:
    """Cari GitHub token dari env var atau file."""
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        return token
    # Coba baca dari file di root project
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for fname in ['2211GHtoken.txt', '.git_token']:
        fpath = os.path.join(root, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                token = f.read().strip()
                if token:
                    return token
    return ''

@app.get('/api/engines')
def api_engines():
    executor = Executor()
    available = executor.get_available_engines()
    return {'engines': available, 'count': len(available)}

@app.get('/api/markets')
def api_markets():
    try:
        index_path = os.path.join(os.path.dirname(__file__), '..', 'pasaran_luna', 'index.json')
        if os.path.exists(index_path):
            with open(index_path, encoding='utf-8') as f:
                index_data = json.load(f)
            market_list = []
            for name, info in index_data.get('markets', {}).items():
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

@app.post('/api/predict')
def api_predict(request: PredictionRequest):
    executor = Executor()
    try:
        result = executor.execute(request.engine, request.market)
        return _build_prediction_response(result, request.engine, request.market)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Prediction failed: {str(e)}')

@app.get('/api/totomacau')
def api_totomacau():
    executor = Executor()
    try:
        result = executor.execute('toto_macau', 'TOTO MACAU')
        return _build_prediction_response(result, 'toto_macau', 'TOTO MACAU')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/api/hongkong_pools')
def api_hongkong_pools():
    executor = Executor()
    try:
        result = executor.execute('hongkong_pools', 'HONGKONG_POOLS')
        return _build_prediction_response(result, 'hongkong_pools', 'HONGKONG_POOLS')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/api/oregon')
def api_oregon_list():
    return {
        'markets': ['OREGON03', 'OREGON06', 'OREGON09', 'OREGON12'],
        'usage': 'POST /api/predict with {"engine":"oregon","market":"OREGON03"}',
    }

@app.get('/api/oregon/{market}')
def api_oregon(market: str):
    valid = ['OREGON03', 'OREGON06', 'OREGON09', 'OREGON12']
    if market not in valid:
        raise HTTPException(status_code=400, detail=f'Invalid. Must be: {valid}')
    executor = Executor()
    try:
        result = executor.execute('oregon', market)
        return _build_prediction_response(result, 'oregon', market)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get('/api/hoki')
def api_hoki():
    try:
        gen = HokiGenerator()
        result = gen.get_hoki()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed: {str(e)}')

# ===== Dual Mode API (alias tanpa prefix /api/) sesuai update_change.md =====
_dual_aliases = [
    ('/status', api_status, ['GET']),
    ('/engines', api_engines, ['GET']),
    ('/markets', api_markets, ['GET']),
    ('/input', api_input, ['POST']),
    ('/predict', api_predict, ['POST']),
    ('/totomacau', api_totomacau, ['GET']),
    ('/oregon', api_oregon_list, ['GET']),
    ('/hoki', api_hoki, ['GET']),
]
for _alias_path, _alias_endpoint, _alias_methods in _dual_aliases:
    app.add_api_route(_alias_path, _alias_endpoint, methods=_alias_methods)

@app.get('/oregon/{market}')
def api_oregon_alias(market: str):
    return api_oregon(market)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8443)
