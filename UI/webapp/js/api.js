const API = {
  BASE: '',

  async get(path) {
    try {
      const r = await fetch(`${API.BASE}${path}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      TGQ.notify(`API Error: ${e.message}`, 'error');
      throw e;
    }
  },

  async post(path, body) {
    try {
      const r = await fetch(`${API.BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return await r.json();
    } catch (e) {
      TGQ.notify(`API Error: ${e.message}`, 'error');
      throw e;
    }
  },

  status() { return API.get('/status'); },
  analyze(data) { return API.post('/analyze', data); },
};
