(() => {
  const page = document.querySelector('#game-page');
  const game = window.POKE_GAMES.find(game=>game.id === page.dataset.game);
  const {esc, toast, favorites} = window.PokeUI;
  function update() {
    const button = page.querySelector('[data-favorite]');
    const favorite = favorites().has(game.id);
    if (button) {
      button.classList.toggle('is-fav',favorite);
      button.textContent = favorite ? '♥ En favoritos' : '♡ Favorito';
      page.querySelector('[data-play]').hidden = !game.owned;
      page.querySelector('[data-howto]').hidden = game.owned;
      page.querySelector('[data-rom]').textContent = game.owned ? game.rom : 'Sin ROM asociada';
      page.querySelector('.rom-row').classList.toggle('missing', !game.owned);
    }
    const form = page.querySelector('#game-configuration');
    if (form && window.PokeSettings.ready()) form.innerHTML = window.PokeSettings.gameForm(game);
  }
  page.querySelector('[data-favorite]')?.addEventListener('click', ()=>{
    const selected = favorites();
    if (selected.has(game.id)) selected.delete(game.id); else selected.add(game.id);
    try { localStorage.setItem('poke-favs',JSON.stringify([...selected])); } catch {}
    update();
  });
  page.querySelector('[data-play]')?.addEventListener('click',async ()=>{
    try { toast(esc((await window.PokeSettings.play(game.id)).message)); }
    catch(error) { toast(esc(error.message),5000); }
  });
  let order = window.POKE_GAMES.map(game=>game.id);
  try {
    const saved = JSON.parse(sessionStorage.getItem('poke-game-order') || 'null');
    if (Array.isArray(saved)) order = saved.filter(id=>window.POKE_GAMES.some(game=>game.id === id));
  } catch {}
  const index = order.indexOf(game.id);
  if (index >= 0 && order.length > 1) page.querySelectorAll('[data-step]').forEach(link=>{
    link.href = `/games/${encodeURIComponent(order[(index+Number(link.dataset.step)+order.length)%order.length])}`;
    link.hidden = false;
  });
  window.addEventListener('poke-library-updated',update);
  update();
})();
