(() => {
  const root = document.querySelector('#pokedex');
  const button = root?.querySelector('#download-pokedex');
  if (!button) return;
  const status = root.querySelector('#pokedex-download-status');
  const count = root.querySelector('#pokedex-download-count');
  const progress = root.querySelector('#pokedex-progress');
  const activity = root.querySelector('#pokedex-sync');
  const endpoint = `/api/pokedex/${encodeURIComponent(root.dataset.game)}`;
  const downloadLabel = button.textContent.trim();
  const completeLabel = root.dataset.ready === 'true' ? 'Completar edición' : downloadLabel;
  let timer, stopped = false;

  function display(state) {
    if (activity) activity.hidden = !['downloading', 'error', 'paused'].includes(state.status);
    status.textContent = state.message || '';
    count.textContent = state.total ? `${state.completed} / ${state.total} Pokémon preparados` : '';
    progress.hidden = state.status === 'empty';
    if (state.total) {
      progress.max = state.total;
      progress.value = state.completed;
    } else {
      progress.removeAttribute('value');
    }
    button.disabled = state.status === 'downloading' || state.status === 'ready';
    button.textContent = state.status === 'downloading' ? 'Descargando…' :
      state.status === 'ready' ? 'Abriendo Pokédex…' :
      ['error', 'paused'].includes(state.status) ? 'Reanudar descarga' : completeLabel;
    if (state.status === 'ready') {
      location.reload();
    } else if (state.status === 'downloading' && !stopped) {
      timer = setTimeout(poll, 1000);
    }
  }

  async function poll() {
    if (stopped) return;
    clearTimeout(timer);
    try {
      const response = await fetch(`${endpoint}/status`);
      if (!response.ok) throw Error('No se pudo consultar el progreso.');
      const state = await response.json();
      if (!stopped) display(state);
    } catch {
      if (!stopped) {
        if (activity) activity.hidden = false;
        status.textContent = 'Esperando conexión con el launcher… El progreso guardado se conserva.';
        timer = setTimeout(poll, 2500);
      }
    }
  }

  button.addEventListener('click', async () => {
    clearTimeout(timer);
    button.disabled = true;
    if (activity) activity.hidden = false;
    status.textContent = 'Preparando descarga…';
    try {
      // Read the current token even if the server was restarted since this page opened.
      const sessionResponse = await fetch('/api/state');
      if (!sessionResponse.ok) throw Error('No se pudo conectar con el launcher.');
      const session = await sessionResponse.json();
      const response = await fetch(`${endpoint}/download`, {
        method:'POST', headers:{'Content-Type':'application/json', 'X-Poke-Token':session.token}, body:'{}'
      });
      const state = await response.json();
      if (!response.ok) throw Error(state.error || 'No se pudo iniciar la descarga.');
      if (!stopped) display(state);
    } catch (error) {
      if (activity) activity.hidden = false;
      status.textContent = error.message;
      button.disabled = false;
      button.textContent = 'Reanudar descarga';
      // The request may have reached the server before the connection failed.
      if (!stopped) timer = setTimeout(poll, 1500);
    }
  });
  window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); });
  poll();
})();
