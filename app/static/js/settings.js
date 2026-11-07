(() => {
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let token = '', config = null, files = {}, activeSystem = 'general', lastScan = null, saving = false;
  const names = {gb:'Game Boy',gbc:'Game Boy Color',gba:'Game Boy Advance',nds:'Nintendo DS','3ds':'Nintendo 3DS'};
  async function request(path, data) {
    const response = await fetch(`/api/${path}`, data === undefined ? {} : {
      method:'POST', headers:{'Content-Type':'application/json','X-Poke-Token':token}, body:JSON.stringify(data)
    });
    const result = await response.json();
    if (!response.ok) throw Error(result.error || 'No se pudo completar la operación.');
    return result;
  }
  async function refresh() {
    const result = await request('state');
    token = result.token; config = result.config;
    for (const game of window.POKE_GAMES) {
      const entry = config.games[game.id];
      game.rom = entry?.rom || null;
      game.owned = Boolean(result.available[game.id]);
    }
    window.dispatchEvent(new Event('poke-library-updated'));
  }
  function unavailable() {
    return '<h2>Configuración local</h2><p>Inicia <code>python server.py</code> y abre <a href="http://127.0.0.1:8765">http://127.0.0.1:8765</a> para configurar carpetas y emuladores.</p>';
  }
  function message(text) {
    const target = document.querySelector('#settings-status');
    if (target) target.textContent = text;
  }
  function gameForm(game) {
    if (!config) return unavailable();
    const system = config.systems[game.consoleKey];
    const current = config.games[game.id]?.rom || '';
    const options = [...new Set([current, ...(files[game.consoleKey] || [])])].filter(Boolean);
    return `<h2>Configuración de ${esc(game.name)}</h2>
      <p>Emulador de ${esc(names[game.consoleKey])}: <strong>${esc(system.emulator || 'Sin configurar')}</strong>. <a href="/settings">Configurar carpetas y emuladores</a></p>
      <form id="game-settings" data-game="${esc(game.id)}" class="settings-form">
      <label>ROM asociada<select name="rom"><option value="">Sin ROM asociada</option>${options.map(path => `<option value="${esc(path)}" ${path === current ? 'selected' : ''}>${esc(path)}</option>`).join('')}</select></label>
      <label>O escribe la ruta completa de otra ROM<input name="manual" placeholder="/ruta/al/juego.gba"></label>
      <p>La asociación es manual: comprueba que el archivo corresponde a este juego. Las variantes detectadas aparecen por separado.</p>
      <div class="settings-actions"><button class="btn btn-primary">Guardar asociación</button><button type="button" class="btn btn-ghost" data-scan>Buscar ROMs en las carpetas</button></div>
      <p id="settings-status" role="status"></p></form>`;
  }
  async function render() {
    const panel = document.querySelector('#settings-page');
    if (!panel) return;
    try {
      const response = await fetch('/settings/fragment?system=' + encodeURIComponent(activeSystem));
      if (!response.ok) throw Error('No se pudo cargar la configuración.');
      panel.innerHTML = await response.text();
      previewRoot(); renderScan();
    } catch (error) { message(error.message); }
  }
  function renderScan() {
    const target = document.querySelector('#scan-results');
    if (!target || !lastScan) return;
    const count = new Set(Object.values(lastScan.files).flat()).size;
    target.innerHTML = `<section class="scan-summary" aria-label="Resultado de la búsqueda">
      <div class="scan-summary-heading"><div><p class="eyebrow">BÚSQUEDA COMPLETADA</p><h3>${count ? `${count} ${count === 1 ? 'archivo encontrado' : 'archivos encontrados'}` : 'Todavía no encontramos ROMs'}</h3></div><a class="btn btn-ghost" href="/">Ir a la biblioteca →</a></div>
      <div class="scan-console-grid">${Object.entries(names).map(([key,name]) => `<div class="scan-console"><span class="system-monogram">${key.toUpperCase()}</span><strong>${lastScan.files[key]?.length || 0}</strong><span>${name}</span></div>`).join('')}</div>
      <p>${count ? `${lastScan.associated?.length || 0} juegos asociados automáticamente a tu colección. Las selecciones existentes se conservan. ${lastScan.ambiguous?.length ? `${lastScan.ambiguous.length} juegos tienen varias ROMs candidatas; elige su versión desde Configuración en la página del juego.` : 'Los archivos sin coincidencia clara siguen disponibles para selección manual.'}` : 'Comprueba la carpeta raíz y los nombres de sus subcarpetas. Después vuelve a guardar y buscar.'}</p>
      ${lastScan.warnings.length ? `<div class="scan-notices"><strong>Carpetas por revisar</strong>${lastScan.warnings.map(warning => `<p>${esc(warning)}</p>`).join('')}</div>` : ''}
      </section>`;
  }
  async function scanSaved() {
    const scanned = await request('scan', {});
    if (!Array.isArray(scanned.associated)) throw Error('El servidor sigue ejecutando una versión anterior. Detén python server.py con Ctrl+C y vuelve a iniciarlo para activar la asociación automática.');
    lastScan = scanned;
    files = lastScan.files;
    await refresh();
    if (location.pathname === '/settings') renderScan();
    else window.dispatchEvent(new Event('poke-library-updated'));
  }
  function previewRoot() {
    const root = document.querySelector('[name="rom_root"]')?.value.trim().replace(/\/+$/, '') || '';
    const preview = document.querySelector('.rom-folder-preview');
    if (preview) preview.innerHTML = `<p class="eyebrow">ESTRUCTURA DE CARPETAS</p>${Object.entries(names).map(([key,name]) => `<div><code>${esc(root ? root + '/' + key : 'Roms/' + key)}</code><span>${name}</span></div>`).join('')}`;
  }
  document.addEventListener('change', event => {
    if (event.target.name !== 'mode') return;
    const field = event.target.closest('[data-system]');
    field.querySelector('[data-browse-emulator]').hidden = event.target.value === 'flatpak';
  });
  document.addEventListener('input', event => { if (event.target.name === 'rom_root') previewRoot(); });
  document.addEventListener('submit', async event => {
    if (!['global-settings','game-settings'].includes(event.target.id)) return;
    event.preventDefault();
    if (saving) return;
    saving = true;
    const global = event.target.id === 'global-settings';
    const submit = event.target.querySelector('button:not([type="button"])');
    if (submit) { submit.disabled = true; submit.textContent = global ? 'Guardando y buscando…' : 'Guardando…'; }
    message(global ? 'Guardando configuración y buscando ROMs…' : 'Guardando asociación…');
    try {
      const next = JSON.parse(JSON.stringify(config));
      if (event.target.id === 'global-settings') {
        next.rom_root = event.target.querySelector('[name="rom_root"]').value.trim();
        for (const field of event.target.querySelectorAll('[data-system]')) {
          const value = name => field.querySelector(`[name="${name}"]`).value.trim();
          next.systems[field.dataset.system] = { folders: value('folders').split('\n').map(x=>x.trim()).filter(Boolean), mode:value('mode'), emulator:value('emulator'), save_folder:value('save_folder') };
        }
      } else {
        const game = window.POKE_GAMES.find(g=>g.id === event.target.dataset.game);
        const form = new FormData(event.target);
        next.games[game.id] = {rom:String(form.get('manual')).trim() || form.get('rom'), system:game.consoleKey};
      }
      await request('config', next);
      if (global) {
        lastScan = null;
        await refresh();
        message('Configuración guardada. Buscando ROMs…');
        await scanSaved();
        message('Configuración guardada y búsqueda completada.');
      } else { await refresh(); message('Asociación guardada.'); }
    } catch (error) { message(error.message); }
    finally {
      saving = false;
      const button = document.querySelector(global ? '#save-and-scan' : '#game-settings button:not([type="button"])');
      if (button) { button.disabled = false; button.textContent = global ? 'Guardar y buscar ROMs' : 'Guardar asociación'; }
    }
  });
  document.addEventListener('click', async event => {
    const emulatorBrowse = event.target.closest('[data-browse-emulator]');
    if (emulatorBrowse) {
      const field = emulatorBrowse.closest('[data-system]');
      emulatorBrowse.disabled = true;
      message('Selecciona el ejecutable del emulador en la ventana del sistema.');
      try {
        const result = await request('browse-emulator', {});
        if (result.path) {
          field.querySelector('[name="emulator"]').value = result.path;
          message('Emulador seleccionado. Pulsa «Guardar y buscar ROMs» para aplicar el cambio.');
        } else message('Selección cancelada.');
      } catch (error) { message(error.message); }
      finally { emulatorBrowse.disabled = false; }
      return;
    }
    const browseSaves = event.target.closest('[data-browse-saves]');
    const browse = browseSaves || event.target.closest('[data-browse-root]');
    if (browse) {
      browse.disabled = true;
      message('Selecciona una carpeta en la ventana del sistema.');
      try {
        const result = await request('browse-folder', {});
        if (result.path) {
          if (browseSaves) browseSaves.closest('[data-system]').querySelector('[name="save_folder"]').value = result.path;
          else {
            document.querySelector('[name="rom_root"]').value = result.path;
            previewRoot();
          }
          message('Carpeta seleccionada. Pulsa «Guardar y buscar ROMs» para aplicarla.');
        } else message('Selección cancelada.');
      } catch (error) { message(error.message); }
      finally { browse.disabled = false; }
      return;
    }
    const tab = event.target.closest('[data-settings-system]');
    if (tab) {
      activeSystem = tab.dataset.settingsSystem;
      document.querySelectorAll('[data-settings-system]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.settingsSystem === activeSystem)));
      document.querySelectorAll('#global-settings [data-settings-panel]').forEach(panel => { panel.hidden = panel.dataset.settingsPanel !== activeSystem; });
      document.querySelectorAll('#global-settings [data-system]').forEach(field => { field.hidden = field.dataset.system !== activeSystem; });
      return;
    }
    const check = event.target.closest('[data-check]');
    const scan = event.target.closest('[data-scan]');
    if (!check && !scan) return;
    try {
      message(check ? 'Comprobando…' : 'Buscando ROMs…');
      if (check) { message((await request('check', {system:check.dataset.check})).message); return; }
      await scanSaved();
      message('Búsqueda completada. Los archivos están disponibles en el selector de ROMs.');
    } catch (error) { message(error.message); }
  });
  window.PokeSettings = { render, gameForm, ready:()=>Boolean(config), async play(id) { return request('play',{game:id}); } };
  previewRoot();
  if (location.protocol !== 'file:') {
    refresh().then(async () => {
      if (config.rom_root || Object.values(config.systems).some(system => system.folders.length)) {
        await scanSaved();
      }
    }).catch(error => {
      window.dispatchEvent(new Event('poke-library-updated'));
      const notification = document.querySelector('#toast');
      if (notification) {
        notification.textContent = error.message;
        notification.classList.add('show');
      }
      message(error.message);
    });
  }
})();
