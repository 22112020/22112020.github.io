(function() {
  ROUTER.route('results', async (container) => {
    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Results</h1>
          <p class="page-subtitle">Riwayat hasil prediksi</p>
        </div>
      </div>

      <div class="search-with-icon">
        <span class="material-icons">search</span>
        <input type="text" id="resultSearch" placeholder="Cari berdasarkan market atau tanggal...">
      </div>

      <div class="card">
        <div class="card-header"><span class="material-icons">history</span> Riwayat Prediksi</div>
        <div class="card-body">
          <div class="empty-state" id="resultEmpty">
            <span class="material-icons">receipt_long</span>
            <p>Belum ada riwayat prediksi.<br>Lakukan analisis terlebih dahulu.</p>
          </div>
          <div id="resultTableContainer" style="display:none">
            <table class="data-table">
              <thead>
                <tr><th>Tanggal</th><th>Market</th><th>Engine</th><th>Hasil</th><th>Status</th></tr>
              </thead>
              <tbody id="resultTableBody"></tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="glass-card" style="padding:20px">
        <div style="display:flex;align-items:center;gap:12px">
          <span class="material-icons" style="color:var(--accent)">bar_chart</span>
          <div>
            <strong style="font-size:13px">Grafik Performa Engine</strong>
            <div style="font-size:11px;color:var(--text-muted);margin-top:2px">Akan tersedia setelah ada data riwayat</div>
          </div>
        </div>
      </div>
    `;
  });
})();
