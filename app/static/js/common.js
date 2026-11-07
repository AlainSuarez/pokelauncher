(() => {
  const data = JSON.parse(document.querySelector('#catalog-data').textContent);
  window.POKE_GAMES = data.games;
  window.POKE_CONSOLES = data.consoles;
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let timer;
  function toast(html, duration=3400) {
    const target = document.querySelector('#toast');
    target.innerHTML = html; target.classList.add('show');
    clearTimeout(timer); timer = setTimeout(()=>target.classList.remove('show'), duration);
  }
  const favorites = () => { try { return new Set(JSON.parse(localStorage.getItem('poke-favs') || '[]')); } catch { return new Set(); } };
  function renderCollection() {
    const games = window.POKE_GAMES;
    const owned = games.filter(game=>game.owned).length;
    document.querySelector('#collection-count').textContent = `${owned} / ${games.length}`;
    document.querySelector('#collection-progress').style.width = `${owned / games.length * 100}%`;
    document.querySelector('#collection-hint').textContent = `${owned} disponibles. Te faltan ${games.length-owned} juegos para completar la colección.`;
    if (document.querySelector('#library-view')) return;
    document.querySelector('#console-nav').innerHTML = data.consoles.map(system=>{
      const list = system.key === 'all' ? games : games.filter(game=>game.consoleKey === system.key);
      return `<a class="nav-item" href="/?console=${system.key}" style="--accent:${system.color}"><span class="nav-icon">${esc(system.short)}</span><span class="nav-text"><strong>${esc(system.name)}</strong><small>${list.filter(game=>game.owned).length} de ${list.length} en colección</small></span><span class="nav-count">${list.length}</span></a>`;
    }).join('');
    const settings = document.querySelector('.settings-link');
    if (location.pathname === '/settings') settings.setAttribute('aria-current','page');
  }
  // Keep bookmarks from the previous hash-based interface working.
  if (location.pathname === '/' || location.pathname === '/index.html') {
    const params = new URLSearchParams(location.hash.slice(1));
    if (location.hash === '#settings') location.replace('/settings');
    else if (params.get('game')) location.replace(`/games/${encodeURIComponent(params.get('game'))}?section=${encodeURIComponent(params.get('section') || 'resumen')}`);
  }
  window.PokeUI = {esc, toast, favorites};
  window.addEventListener('poke-library-updated', renderCollection);
  renderCollection();
  document.addEventListener('error', event=>{
    if (event.target.tagName === 'IMG') { event.target.style.display='none'; event.target.parentElement.classList.add('no-cover'); }
  }, true);
})();
