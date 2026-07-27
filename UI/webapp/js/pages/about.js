(function() {
  ROUTER.route('about', async (container) => {
    let status = null;
    try { status = await API.status(); } catch (e) {}

    container.innerHTML = `
      <div class="card card-about">
        <div class="about-hero gradient-border">
          <img src="img/tgq-logo.svg" alt="TGQ" class="about-logo">
          <h2>TGQ</h2>
          <p class="about-tagline">Togel Prediction Engine — AI-Powered</p>
        </div>
        <div class="about-content">
          <p>
            <strong>TGQ</strong> adalah sistem prediksi togel berbasis AI yang berjalan di
            <strong>Samsung Galaxy Note 8</strong> (Snapdragon 835, aarch64) menggunakan
            Termux native + Python 3.14.
          </p>

          <div class="about-features">
            <div class="feature-item">
              <span class="material-icons">memory</span>
              <div>
                <strong>3 Engine</strong>
                <small>Oregon, Toto Macau, Historical Trend</small>
              </div>
            </div>
            <div class="feature-item">
              <span class="material-icons">business</span>
              <div>
                <strong>46 Markets</strong>
                <small>Pasar togel aktif</small>
              </div>
            </div>
            <div class="feature-item">
              <span class="material-icons">checklist</span>
              <div>
                <strong>98 Tests</strong>
                <small>Unit test passing</small>
              </div>
            </div>
          </div>

          <div class="about-footer" style="text-align:center;padding:18px 0 0;border-top:1px solid var(--border);font-size:11px;color:var(--text-muted);margin-top:24px">
            <p>TGQ v2.0 &mdash; Native Termux &mdash; ${new Date().getFullYear()}</p>
            <p style="margin-top:4px">Built with FastAPI + Vanilla JS SPA</p>
          </div>
        </div>
      </div>
    `;
  });
})();
