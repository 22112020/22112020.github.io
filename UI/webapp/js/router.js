const ROUTER = {
  routes: {},
  current: null,

  route(name, render) {
    ROUTER.routes[name] = render;
  },

  async navigate(hash) {
    const path = hash.replace(/^#\//, '') || 'dashboard';
    TGQ.state.previousRoute = ROUTER.current;
    ROUTER.current = path;

    document.querySelectorAll('.nav-item, .bottom-nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.route === path);
    });

    const container = document.getElementById('pageContainer');
    container.innerHTML = '';

    TGQ.loading(true);
    try {
      if (ROUTER.routes[path]) {
        await ROUTER.routes[path](container);
      } else {
        container.innerHTML = `<div class="empty-state"><span class="material-icons">error_outline</span><p>Halaman tidak ditemukan</p></div>`;
      }
    } finally {
      TGQ.loading(false);
    }

    container.scrollTop = 0;
    window.scrollTo(0, 0);
  },

  init() {
    window.addEventListener('hashchange', () => ROUTER.navigate(location.hash));
    ROUTER.navigate(location.hash || '#/dashboard');
  }
};
