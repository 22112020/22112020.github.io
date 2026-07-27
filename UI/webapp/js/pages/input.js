(function() {
  ROUTER.route('input', async (container) => {
    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Input Data</h1>
          <p class="page-subtitle">Input manual data hasil dan trash</p>
        </div>
      </div>

      <div class="info-box">
        <span class="material-icons">info</span>
        <div>Gunakan halaman ini untuk memasukkan data hasil togel atau mengelola data <em>trash</em>.<br>
        Format: <strong>tanggal|market|angka</strong> (satu per baris)</div>
      </div>

      <div class="card">
        <div class="card-header"><span class="material-icons">edit_note</span> Input Hasil Baru</div>
        <div class="card-body">
          <div class="form-group">
            <label class="form-label">Data Hasil (format: tanggal|market|angka)</label>
            <textarea id="inputData" placeholder="Contoh:&#10;27-07-2026|OREGON03|1234&#10;27-07-2026|TOTOMACAU|5678"></textarea>
          </div>
          <div class="textarea-footer">
            <span class="line-counter" id="lineCounter">0 baris</span>
            <div class="textarea-actions">
              <button class="btn btn-outline btn-sm" onclick="document.getElementById('inputData').value='';updateLineCount()">
                <span class="material-icons">clear</span> Clear
              </button>
              <button class="btn btn-accent btn-sm" onclick="submitInput()">
                <span class="material-icons">upload</span> Submit
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card" style="padding:20px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <span class="material-icons" style="color:var(--accent)">delete</span>
          <strong style="font-size:13px">Trash Dashboard</strong>
        </div>
        <p style="font-size:12px;color:var(--text-muted);line-height:1.6">
          Data trash digunakan untuk menampung hasil yang tidak valid atau perlu ditinjau ulang.<br>
          Fitur ini akan tersedia setelah integrasi backend selesai.
        </p>
      </div>
    `;

    const ta = document.getElementById('inputData');
    window.updateLineCount = () => {
      const lines = ta.value.split('\n').filter(l => l.trim()).length;
      document.getElementById('lineCounter').textContent = `${lines} baris`;
    };
    ta.addEventListener('input', window.updateLineCount);

    window.submitInput = async () => {
      const data = ta.value.trim();
      if (!data) { TGQ.notify('Masukkan data terlebih dahulu', 'error'); return; }
      TGQ.notify('Data akan diproses. Fitur ini dalam pengembangan.', 'error');
    };
  });
})();
