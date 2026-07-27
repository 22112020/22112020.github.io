(function() {
  ROUTER.route('markets', async (container) => {
    let status = null;
    try { status = await API.status(); } catch (e) {}

    container.innerHTML = `
      <div class="page-header">
        <div>
          <h1 class="page-title">Markets</h1>
          <p class="page-subtitle">${status?.markets ?? '46'} pasar togel aktif</p>
        </div>
        <div class="page-actions"></div>
      </div>

      <div class="search-with-icon">
        <span class="material-icons">search</span>
        <input type="text" id="marketSearch" placeholder="Cari market..." oninput="filterMarkets(this.value)">
      </div>

      <div class="market-grid" id="marketGrid">
        <div class="empty-state">
          <span class="material-icons">hourglass_top</span>
          <p>Memuat data market...</p>
        </div>
      </div>
    `;

    let markets = [];
    try {
      if (status && status.market_list) {
        markets = status.market_list;
      }
    } catch (e) {}

    const grid = document.getElementById('marketGrid');
    grid.innerHTML = '';

    if (markets.length === 0) {
      grid.innerHTML = `<div class="empty-state"><span class="material-icons">search_off</span><p>Tidak ada data market tersedia</p></div>`;
      return;
    }

    window.filterMarkets = (q) => {
      const items = grid.querySelectorAll('.market-tag');
      const val = q.toLowerCase().trim();
      items.forEach(el => {
        const name = el.dataset.name || '';
        el.style.display = (!val || name.includes(val)) ? '' : 'none';
      });
    };

    markets.forEach(m => {
      const tag = document.createElement('div');
      tag.className = 'market-tag';
      tag.dataset.name = m.toLowerCase();
      tag.innerHTML = `
        <div class="market-name">${m}</div>
        <div class="market-result pending">---</div>
        <div class="market-period">Klik untuk detail</div>
      `;
      tag.onclick = () => {
        const params = new URLSearchParams({ market: m });
        location.hash = `#/analysis?market=${encodeURIComponent(m)}`;
      };
      grid.appendChild(tag);
    });
  });
})();
