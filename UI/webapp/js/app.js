const API = window.location.origin;

// NAV
document.querySelectorAll('.nav-links a').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.nav-links a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + a.dataset.page).classList.add('active');
  });
});

// ENGINE SELECT → MARKET OPTIONS
document.getElementById('predictEngine').addEventListener('change', function() {
  const sel = document.getElementById('predictMarket');
  sel.innerHTML = this.value === 'toto_macau'
    ? '<option value="TOTO MACAU">TOTO MACAU</option>'
    : '<option value="OREGON03">OREGON03</option><option value="OREGON06">OREGON06</option><option value="OREGON09">OREGON09</option><option value="OREGON12">OREGON12</option>';
});

// INIT
document.addEventListener('DOMContentLoaded', async () => {
  await loadDashboard();
  await loadMarkets();
});

async function loadDashboard() {
  try {
    const r = await fetch(`${API}/status`);
    const data = await r.json();
    document.getElementById('sysStatus').textContent = 'ONLINE';
    document.getElementById('sysStatus').className = 'stat-value online';
    document.getElementById('sysEngines').textContent = (data.engines || '-').toString();
    document.getElementById('sysMarkets').textContent = (data.markets || '-').toString();
    document.getElementById('sysSync').textContent = data.last_sync || '-';
  } catch {
    document.getElementById('sysStatus').textContent = 'OFFLINE';
    document.getElementById('sysStatus').className = 'stat-value warn';
  }
}

async function loadMarkets() {
  // Static market list
  const markets = [
    '4DTOTOMACAU','5DTOTOMACAU','BANGKOK0130','BANGKOK0930','BRUNEI02','BRUNEI14','BRUNEI21',
    'BULLSEYE','CALIFORNIA','CAROLINADAY','CAROLINAEVE','CHELSEA11','CHELSEA15','CHELSEA19',
    'CHELSEA21','FLORIDAEVE','FLORIDAMID','JAKARTA1400','JAKARTA2330','KENTUCKYEVE','KENTUCKYMID',
    'KINGKONG4D','MAGNUM4D','NEVADA','NEWYORKEVE','NEWYORKMID','OREGON03','OREGON06','OREGON09',
    'OREGON12','PCSO','SINGAPORE',
    'HOKIDRAW','HUAHIN0100','CAMBODIALOTTO','POIPET12','SYDNEYLOTTO','POIPET15','TOTOMALI1530',
    'HUAHIN1630','POIPET19','TOTOMALI2030','HUAHIN2100','POIPET22','HONGKONGLOTTO','TOTOMALI2330'
  ];
  const grid = document.getElementById('marketGrid');
  grid.innerHTML = markets.map(m => `<div class="market-tag">${m}</div>`).join('');
}

function filterMarkets() {
  const q = document.getElementById('marketSearch').value.toUpperCase();
  document.querySelectorAll('.market-tag').forEach(el => {
    el.style.display = el.textContent.includes(q) ? '' : 'none';
  });
}

// PREDICT
async function runPrediction() {
  const engine = document.getElementById('predictEngine').value;
  const market = document.getElementById('predictMarket').value;
  await doPredict(engine, market, 'predictResult');
}

async function predictTotoMacau() {
  const r = await doPredict('toto_macau', 'TOTO MACAU', 'latestResult');
  switchPage('dashboard');
}

async function predictOregon(market) {
  const r = await doPredict('oregon', market, 'latestResult');
  switchPage('dashboard');
}

async function doPredict(engine, market, resultId) {
  const box = document.getElementById(resultId);
  box.innerHTML = '<div><span class="spinner"></span>Memproses...</div>';
  box.classList.add('show');

  try {
    const r = await fetch(`${API}/analyze`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({engine, market})
    });
    const data = await r.json();

    if (data.error) {
      box.innerHTML = `<div style="color:#f44;text-align:center">${data.error}</div>`;
      return null;
    }

    const main = (data.prediction?.main || []).join(' ');
    const backup = data.prediction?.backup?.[0] || '-';
    const period = data.target_period || '-';
    const conf = data.confidence ? (data.confidence * 100).toFixed(0) : '-';

    box.innerHTML = `
      <div class="result-digits">${main}</div>
      <div class="result-meta">
        ${data.market} · Periode ${period} · Backup ${backup}
        ${conf !== '-' ? `· Confidence ${conf}%` : ''}
      </div>
      <div class="result-detail">Engine: ${data.engine} · Target: ${data.target_period}</div>
    `;

    if (resultId === 'latestResult') {
      document.getElementById('latestResult').innerHTML = `
        <div class="result-digits" style="font-size:32px">${main}</div>
        <div class="result-meta">${data.market} · Periode ${period} · Backup ${backup}</div>
      `;
    }

    return data;
  } catch(e) {
    box.innerHTML = `<div style="color:#f44;text-align:center">Connection error: ${e.message}</div>`;
    return null;
  }
}

function switchPage(name) {
  document.querySelectorAll('.nav-links a').forEach(x => x.classList.remove('active'));
  document.querySelector(`.nav-links a[data-page="${name}"]`)?.classList.add('active');
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-' + name)?.classList.add('active');
}
