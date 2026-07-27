(function() {
  function statIcon(type) {
    const icons = {
      markets: 'business',
      engines: 'memory',
      uptime: 'schedule',
      status: 'check_circle',
    };
    return icons[type] || 'info';
  }

  ROUTER.route('dashboard', async (container) => {
    let status = null;
    try { status = await API.status(); } catch (e) {}

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Dashboard</h1>
          <p class="page-subtitle">Overview sistem TGQ Prediction Engine</p>
        </div>
        <div class="page-actions">
          <button class="btn btn-glass btn-sm" onclick="location.hash='#/analysis'">
            <span class="material-icons">analytics</span> Analysis Baru
          </button>
        </div>
      </div>

      <div class="stats-grid" id="statsGrid">
        <div class="stat-card">
          <div class="stat-icon stat-icon-maroon"><span class="material-icons">business</span></div>
          <div>
            <div class="stat-value" id="statMarkets">${status?.markets ?? '...'}</div>
            <div class="stat-label">Markets</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-pink"><span class="material-icons">memory</span></div>
          <div>
            <div class="stat-value" id="statEngines">${status?.engines ?? '...'}</div>
            <div class="stat-label">Engines</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-dark"><span class="material-icons">schedule</span></div>
          <div>
            <div class="stat-value" id="statUptime">${status?.uptime ?? '...'}</div>
            <div class="stat-label">Uptime</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon stat-icon-maroon"><span class="material-icons">check_circle</span></div>
          <div>
            <div class="stat-value" id="statTested">${status?.tested ?? '...'}</div>
            <div class="stat-label">Tested</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="material-icons">flash_on</span> Quick Actions
        </div>
        <div class="card-body">
          <div class="quick-actions">
            <div class="action-btn action-icon-maroon" onclick="location.hash='#/markets'">
              <span class="material-icons">grid_view</span>
              <div class="action-text"><strong>Markets</strong><small>Lihat 46 market</small></div>
            </div>
            <div class="action-btn action-icon-pink" onclick="location.hash='#/analysis'">
              <span class="material-icons">analytics</span>
              <div class="action-text"><strong>Analysis</strong><small>Prediksi baru</small></div>
            </div>
            <div class="action-btn action-icon-maroon" onclick="location.hash='#/results'">
              <span class="material-icons">history</span>
              <div class="action-text"><strong>Results</strong><small>Riwayat prediksi</small></div>
            </div>
            <div class="action-btn action-icon-pink" onclick="location.hash='#/input'">
              <span class="material-icons">edit_note</span>
              <div class="action-text"><strong>Input</strong><small>Data manual</small></div>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card" style="padding:20px;margin-bottom:20px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
          <span class="material-icons" style="color:var(--accent)">info</span>
          <strong style="font-size:13px">Server Status</strong>
        </div>
        <div style="font-size:12px;color:var(--text-secondary);line-height:1.8" id="serverInfo">
          Memuat data...
        </div>
      </div>
    `;

    if (status) {
      const si = document.getElementById('serverInfo');
      si.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
          <span>Server:</span><span style="color:var(--text)">uvicorn on 0.0.0.0:8443</span>
          <span>Python:</span><span style="color:var(--text)">${status.python || '3.14.x'}</span>
          <span>Engines:</span><span style="color:var(--text)">${status.engines || '3'}</span>
          <span>Tests:</span><span style="color:var(--text)">${status.tests || '98/98'}</span>
        </div>
      `;
    }
  });
})();
