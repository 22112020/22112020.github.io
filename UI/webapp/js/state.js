const TGQ = {
  state: {
    status: null,
    markets: [],
    selectedEngine: 'oregon',
    loading: false,
    previousRoute: null,
    notyf: null,
  },

  init() {
    TGQ.state.notyf = new Notyf({
      duration: 3000,
      position: { x: 'right', y: 'top' },
      ripple: false,
      types: [
        { type: 'success', background: 'linear-gradient(135deg, #8B1A1A, #5C1010)', icon: false },
        { type: 'error', background: 'linear-gradient(135deg, #E91E63, #C0184A)', icon: false },
      ]
    });
  },

  notify(msg, type = 'success') {
    TGQ.state.notyf.open({ type, message: msg });
  },

  loading(show) {
    const el = document.getElementById('loadingOverlay');
    if (!el) return;
    el.classList.toggle('show', show);
    TGQ.state.loading = show;
  }
};
