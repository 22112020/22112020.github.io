(function() {
  ROUTER.route('analysis', async (container) => {
    const params = new URLSearchParams(location.hash.split('?')[1] || '');
    const preMarket = params.get('market') || '';

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Analysis</h1>
          <p class="page-subtitle">Prediksi angka togel dengan engine AI</p>
        </div>
      </div>

      <div class="info-box">
        <span class="material-icons">lightbulb</span>
        <div>Pilih engine dan masukkan data untuk mendapatkan prediksi angka.<br>
        <strong>Engine tersedia:</strong> Oregon, Toto Macau, Historical Trend</div>
      </div>

      <div class="card">
        <div class="card-header"><span class="material-icons">tune</span> Konfigurasi</div>
        <div class="card-body">
          <div class="engine-selector" id="engineSelector">
            <label class="engine-option">
              <input type="radio" name="engine" value="oregon" checked>
              <div class="engine-card">
                <span class="material-icons">bolt</span>
                <strong>Oregon</strong>
                <small>Prediksi berbasis pola Oregon</small>
              </div>
            </label>
            <label class="engine-option">
              <input type="radio" name="engine" value="toto_macau">
              <div class="engine-card">
                <span class="material-icons">casino</span>
                <strong>Toto Macau</strong>
                <small>Prediksi Toto Macau 4D/5D</small>
              </div>
            </label>
            <label class="engine-option">
              <input type="radio" name="engine" value="historical_trend">
              <div class="engine-card">
                <span class="material-icons">trending_up</span>
                <strong>Historical Trend</strong>
                <small>Analisis tren historis</small>
              </div>
            </label>
          </div>

          <div class="form-group" style="margin-top:16px">
            <label class="form-label">Market</label>
            <input class="form-input" id="analysisMarket" placeholder="Contoh: OREGON03" value="${preMarket}">
          </div>

          <div class="form-group">
            <label class="form-label">Data / Konteks</label>
            <textarea id="analysisData" placeholder="Masukkan data yang akan dianalisis..."></textarea>
          </div>

          <button class="btn btn-accent btn-lg btn-block" onclick="runAnalysis()">
            <span class="material-icons">auto_awesome</span> Generate Prediksi
          </button>
        </div>
      </div>

      <div class="result-box" id="resultBox">
        <div class="result-digits" id="resultDigits">--</div>
        <div class="result-meta" id="resultMeta"></div>
        <div class="result-detail" id="resultDetail"></div>
        <div class="result-confidence" id="resultConfidence"></div>
      </div>
    `;

    window.runAnalysis = async () => {
      const engine = document.querySelector('input[name="engine"]:checked')?.value || 'oregon';
      const market = document.getElementById('analysisMarket').value.trim();
      const data = document.getElementById('analysisData').value.trim();

      if (!market) { TGQ.notify('Masukkan nama market', 'error'); return; }

      const btn = document.querySelector('.btn-accent');
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Memproses...';

      TGQ.loading(true);
      try {
        const result = await API.analyze({
          engine,
          market: market.toUpperCase(),
          data: data || undefined,
        });

        const box = document.getElementById('resultBox');
        box.classList.add('show');

        document.getElementById('resultDigits').textContent = result.digits || result.prediction || (result.numbers ? result.numbers.join(' ') : '--');
        document.getElementById('resultMeta').textContent = `Engine: ${engine} | Market: ${market.toUpperCase()}`;
        document.getElementById('resultDetail').textContent = result.detail || result.message || '';
        document.getElementById('resultConfidence').innerHTML = result.confidence
          ? `<div>Confidence</div><div class="bar"><div class="bar-fill" style="width:${result.confidence}%"></div></div><span style="font-size:12px;color:var(--text-muted)">${result.confidence}%</span>`
          : '';

        TGQ.notify('Prediksi berhasil!', 'success');
      } catch (e) {
        document.getElementById('resultBox').classList.remove('show');
      } finally {
        TGQ.loading(false);
        btn.disabled = false;
        btn.innerHTML = '<span class="material-icons">auto_awesome</span> Generate Prediksi';
      }
    };
  });
})();
