(() => {
  const root = document.querySelector('#save-view');
  if (!root) return;
  const {esc} = window.PokeUI;
  const form = root.querySelector('#save-form');
  const button = root.querySelector('#read-save');
  const status = root.querySelector('#save-status');
  const result = root.querySelector('#save-result');
  const select = root.querySelector('#detected-saves');
  const endpoint = `/api/saves/${encodeURIComponent(root.dataset.game)}`;
  let token = '', ready = false, loading = false, shownPath = '';
  async function json(response) {
    const data = await response.json();
    if (!response.ok) throw Error(data.error || 'No se pudo consultar la partida.');
    return data;
  }
  const date = value => new Date(value).toLocaleString();
  let current = null, boxIndex = 0, slot = null;
  const ball = '<span class="save-ball" aria-hidden="true"></span>';
  function art(p, compact = false) {
    const visual = p.visual || {};
    const image = compact ? visual.sprite || visual.artwork : visual.artwork || visual.sprite;
    return `<span class="save-art${p.is_egg ? ' save-egg' : ''}">${ball}${image && !p.is_egg ? `<img src="${esc(image)}" alt="Ilustración de ${esc(p.species_name)}" ${compact ? 'loading="lazy"' : ''} width="160" height="160">` : ''}</span>`;
  }
  function types(p) {
    return `<span class="pokemon-types">${(p.visual?.types || []).map(type => `<span class="pokemon-type type-${esc(type.slug)}">${esc(type.name)}</span>`).join('')}</span>`;
  }
  function traits(p) {
    return `<div class="save-traits"><span>Objeto equipado<strong>${esc(p.held_item || 'Sin objeto')}</strong></span><span>Forma<strong>${p.is_egg ? 'Huevo' : esc(p.form || 'Normal')}</strong></span></div>
      <span class="save-field-label">Movimientos</span><ul class="save-moves">${p.moves.map(move => `<li>${esc(move)}</li>`).join('') || '<li>Sin movimientos</li>'}</ul>`;
  }
  function pokemon(p) {
    return `<li class="save-pokemon${p.shiny ? ' is-shiny' : ''}"><div class="save-card-top"><span>#${String(p.species).padStart(3, '0')}</span><span class="save-level">Nv. ${esc(p.level)}</span></div>
      ${p.shiny ? '<span class="save-shiny" title="Pokémon variocolor" aria-label="Variocolor">✦</span>' : ''}${art(p)}
      <div class="save-card-name"><h4>${esc(p.is_egg ? 'Huevo' : p.nickname)}</h4><span>${esc(p.species_name)}</span></div>${types(p)}
      <details class="save-card-details"><summary>Movimientos y objeto</summary>${traits(p)}</details></li>`;
  }
  function capacity(box) {
    return box.capacity || (current.generation < 3 ? Math.max(20, ...box.pokemon.map(p => p.slot)) : 30);
  }
  const boxName = box => box.name || `Caja ${box.number}`;
  function renderBox() {
    const box = current?.boxes[boxIndex];
    if (!box) return;
    const target = result.querySelector('#save-box-content');
    const slots = new Map(box.pokemon.map(p => [p.slot, p]));
    const count = capacity(box);
    target.innerHTML = `<div class="save-storage"><div class="save-box-grid${count === 20 ? ' save-box-grid-gb' : ''}" role="group" aria-label="Pokémon de ${esc(boxName(box))}">${Array.from({length:count}, (_, index) => {
      const position = index + 1, p = slots.get(position);
      return p ? `<button type="button" class="save-slot" data-slot="${position}" aria-pressed="${slot === position}" aria-label="${esc(p.nickname)}, ${esc(p.species_name)}, nivel ${p.level}, posición ${position}"><span class="save-slot-number">${position}</span>${art(p, true)}${p.shiny ? '<span class="save-slot-shiny" aria-label="Variocolor">✦</span>' : ''}<span class="save-slot-name">${esc(p.is_egg ? 'Huevo' : p.species_name)}</span></button>`
        : `<div class="save-slot is-empty" aria-label="Posición ${position} vacía"><span class="save-slot-number">${position}</span>${ball}</div>`;
    }).join('')}</div><aside class="save-box-inspector" aria-live="polite"></aside></div>`;
    result.querySelector('#save-box-select').value = String(boxIndex);
    result.querySelector('[data-box-step="-1"]').disabled = boxIndex === 0;
    result.querySelector('[data-box-step="1"]').disabled = boxIndex === current.boxes.length - 1;
    renderInspector();
  }
  function renderInspector() {
    const box = current.boxes[boxIndex];
    const p = box.pokemon.find(p => p.slot === slot);
    const target = result.querySelector('.save-box-inspector');
    target.innerHTML = p ? `<div class="save-inspector-heading"><span class="eyebrow">${esc(boxName(box))} · POSICIÓN ${p.slot}</span><span class="save-level">Nv. ${esc(p.level)}</span></div>${art(p)}
      <h4>${esc(p.is_egg ? 'Huevo' : p.nickname)}${p.shiny ? ' <span class="save-inspector-shiny" title="Variocolor">✦</span>' : ''}</h4><p>${esc(p.species_name)} · #${String(p.species).padStart(3, '0')}</p>${types(p)}${traits(p)}
      ${p.form || p.shiny ? '<small class="save-art-caption">Ilustración de la especie</small>' : ''}`
      : `<div class="save-inspector-empty">${ball}<h4>${box.pokemon.length ? 'Conoce a tus Pokémon' : 'Espacio para nuevas aventuras'}</h4><p>${box.pokemon.length ? 'Selecciona un Pokémon de la caja para ver sus datos.' : 'Esta caja todavía está vacía.'}</p></div>`;
    result.querySelectorAll('[data-slot]').forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.slot) === slot)));
  }
  function render(data) {
    const previousBox = current?.source.path === data.source.path ? boxIndex : -1;
    current = data;
    const stored = data.boxes.reduce((sum, box) => sum + box.pokemon.length, 0);
    const occupied = data.boxes.filter(box => box.pokemon.length).length;
    const battle = data.battle_box;
    const battleSlots = new Map((battle?.pokemon || []).map(p => [p.slot, p]));
    boxIndex = previousBox >= 0 && previousBox < data.boxes.length ? previousBox : Math.max(0, data.boxes.findIndex(box => box.pokemon.length));
    slot = data.boxes[boxIndex]?.pokemon[0]?.slot ?? null;
    result.innerHTML = `<section class="save-trainer" aria-label="Ficha de entrenador"><div class="save-trainer-identity"><div class="save-trainer-emblem" aria-hidden="true">${ball}<span>${esc(Array.from(data.trainer.name)[0] || '?')}</span></div><div><span class="eyebrow">${esc(root.dataset.region)} · ${esc(root.dataset.name)}</span><h3>${esc(data.trainer.name)}</h3><span class="save-trainer-id">Entrenador · ID ${esc(data.trainer.id)}</span></div></div>
      <dl class="save-metrics"><div><dt>Tiempo jugado</dt><dd>${esc(data.trainer.play_time)}</dd></div><div><dt>En tu equipo</dt><dd>${data.party.length}<small> / 6</small></dd></div><div><dt>En tus cajas</dt><dd>${stored}</dd></div></dl></section>
      ${data.edition_ambiguous ? '<p class="save-notice">Este guardado comparte formato con otra edición. Comprueba que corresponde a este juego.</p>' : ''}
      <section class="save-team" aria-labelledby="save-team-title"><header class="save-section-heading"><div><span class="eyebrow">TUS COMPAÑEROS</span><h3 id="save-team-title">Equipo de aventura <span>${data.party.length}</span></h3></div><p>Siempre a tu lado.</p></header><ul class="save-team-grid">${data.party.map(pokemon).join('') || '<li class="save-empty-message">Tu próximo compañero te espera. El equipo está vacío.</li>'}</ul></section>
      ${battle ? `<section class="save-battle" aria-labelledby="save-battle-title"><header class="save-section-heading"><div><span class="eyebrow">LISTOS PARA COMBATIR</span><h3 id="save-battle-title">Caja de Combate <span>${battle.pokemon.length} / ${battle.capacity}</span></h3></div><p>${battle.locked ? 'Equipo bloqueado para una competición' : 'Tu equipo de competición'}</p></header><ul class="save-team-grid">${Array.from({length:battle.capacity}, (_, index) => {
        const p = battleSlots.get(index + 1);
        return p ? pokemon(p) : `<li class="save-pokemon save-battle-empty">${ball}<span>Posición ${index + 1}</span><strong>Libre</strong></li>`;
      }).join('')}</ul></section>` : ''}
      ${['x', 'y'].includes(root.dataset.game) && !data.storage ? '<p class="save-notice">Pulsa Actualizar para cargar la Caja de Combate y las cajas disponibles de esta partida.</p>' : ''}
      <section class="save-boxes" aria-labelledby="save-boxes-title"><header class="save-section-heading"><div><span class="eyebrow">TU COLECCIÓN</span><h3 id="save-boxes-title">Cajas Pokémon</h3></div><p>${occupied} de ${data.storage?.unlocked_boxes ?? data.boxes.length} cajas disponibles con Pokémon</p></header>
      ${data.boxes.length ? `<div class="save-box-toolbar"><span class="save-box-caption">Elige una caja y explora tus Pokémon</span><div class="save-box-navigation"><button type="button" class="btn btn-ghost" data-box-step="-1" aria-label="Caja anterior">‹</button><label for="save-box-select" class="save-sr-only">Caja</label><select id="save-box-select">${data.boxes.map((box, index) => `<option value="${index}">${esc(boxName(box))}${box.unlocked === false ? ' (sin desbloquear)' : ''} · ${box.pokemon.length} / ${capacity(box)}</option>`).join('')}</select><button type="button" class="btn btn-ghost" data-box-step="1" aria-label="Caja siguiente">›</button></div></div><div id="save-box-content"></div>` : '<p>Esta partida no tiene cajas disponibles.</p>'}</section>
      <p class="save-timestamps">Guardado: ${esc(date(data.source.modified_at))} <span aria-hidden="true">·</span> Última lectura: ${esc(date(data.source.read_at))}</p>`;
    if (data.boxes.length) renderBox();
    root.querySelector('#save-art-note').hidden = ![...data.party, ...data.boxes.flatMap(box => box.pokemon), ...(battle?.pokemon || [])].some(p => !p.is_egg && !p.visual?.artwork && !p.visual?.sprite);
  }
  result.addEventListener('click', event => {
    const step = event.target.closest('[data-box-step]');
    if (step) {
      boxIndex = Math.max(0, Math.min(current.boxes.length - 1, boxIndex + Number(step.dataset.boxStep)));
      slot = current.boxes[boxIndex].pokemon[0]?.slot ?? null;
      renderBox();
    }
    const chosen = event.target.closest('[data-slot]');
    if (chosen) { slot = Number(chosen.dataset.slot); renderInspector(); }
  });
  result.addEventListener('change', event => {
    if (event.target.id !== 'save-box-select') return;
    boxIndex = Number(event.target.value);
    slot = current.boxes[boxIndex].pokemon[0]?.slot ?? null;
    renderBox();
  });
  async function read() {
    if (loading || !ready || !select.value) return;
    loading = true;
    button.disabled = select.disabled = true;
    root.setAttribute('aria-busy', 'true');
    status.textContent = 'Cargando…';
    button.textContent = 'Cargando…';
    try {
      const data = await json(await fetch(endpoint, {method:'POST', headers:{'Content-Type':'application/json', 'X-Poke-Token':token}, body:JSON.stringify({path:select.value})}));
      render(data);
      shownPath = data.source.path;
      status.textContent = 'Partida cargada. Puedes seguir jugando y actualizar cuando quieras.';
    } catch (error) {
      status.textContent = `${error.message}${result.childElementCount ? ' Se sigue mostrando la última partida cargada.' : ''}`;
    } finally {
      loading = false;
      button.disabled = !ready || !select.value;
      select.disabled = false;
      button.textContent = 'Actualizar';
      root.removeAttribute('aria-busy');
    }
  }
  form.addEventListener('submit', event => { event.preventDefault(); read(); });
  select.addEventListener('change', () => {
    if (select.value !== shownPath) read();
  });
  (async () => {
    try {
      const [state, data] = await Promise.all([fetch('/api/state').then(json), fetch(endpoint).then(json)]);
      token = state.token;
      ready = data.ready;
      const entries = data.detected;
      select.innerHTML = (entries.length > 1 ? '<option value="">Elige una partida</option>' : '') + entries.map((item, index) =>
        `<option value="${esc(item.path)}">Partida ${index + 1} · ${esc(date(item.modified_at))}</option>`).join('');
      if (!entries.length) select.innerHTML = '<option value="">Sin partidas disponibles</option>';
      if (entries.some(item => item.path === data.path)) select.value = data.path;
      select.disabled = !entries.length;
      button.disabled = !ready || !select.value;
      root.querySelector('#save-settings-link').hidden = entries.length > 0;
      if (data.snapshot) {
        render(data.snapshot);
        shownPath = data.snapshot.source.path;
      }
      if (data.snapshot?.reader_refresh_error) status.textContent = 'No se pudo actualizar la información de la copia guardada. Pulsa Actualizar para volver a cargar la partida.';
      else if (!ready) status.textContent = 'El lector de partidas no está disponible.';
      else if (!entries.length) status.textContent = data.snapshot ? 'Mostrando la última partida cargada.' : '';
      else if (data.snapshot) status.textContent = 'Mostrando la última partida cargada. Pulsa Actualizar para renovarla.';
      else if (select.value) await read();
      else status.textContent = 'Elige la partida que quieres consultar.';
    } catch (error) { status.textContent = error.message; }
  })();
})();
