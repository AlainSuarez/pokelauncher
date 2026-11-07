(() => {
  "use strict";

  const games = window.POKE_GAMES || [];
  const consoles = window.POKE_CONSOLES || [];
  const consoleMap = Object.fromEntries(consoles.map((c) => [c.key, c]));
  const $ = (sel) => document.querySelector(sel);
  const storage = {
    get(key, fallback = null) { try { return localStorage.getItem(key); } catch { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* file:// sin storage */ } }
  };
  const readFavorites = () => {
    try { return new Set(JSON.parse(storage.get("poke-favs") || "[]")); }
    catch { return new Set(); }
  };

  const state = {
    console: "all",
    filter: "all",
    search: "",
    sort: "release",
    view: storage.get("poke-view") || "grid",
    favorites: readFavorites(),
  };

  const el = {
    nav: $("#console-nav"),
    grid: $("#game-grid"),
    title: $("#page-title"),
    subtitle: $("#page-subtitle"),
    collectionCount: $("#collection-count"),
    collectionProgress: $("#collection-progress"),
    collectionHint: $("#collection-hint"),
    resultCount: $("#result-count"),
    filterChips: $("#filter-chips"),
    search: $("#search"),
    sort: $("#sort"),
    viewBtn: $("#view-btn"),
    randomBtn: $("#random-btn"),
    empty: $("#empty-state"),
    clearFilters: $("#clear-filters"),
    toast: $("#toast")
  };

  const normalize = (value) =>
    String(value)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();

  const escapeHtml = (value) =>
    String(value).replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[ch]));

  const generationNumber = (roman) => ({ I: 1, II: 2, III: 3, IV: 4, V: 5, VI: 6, VII: 7 }[roman] || 0);
  const consoleOf = (game) => consoleMap[game.consoleKey] || consoles[0];
  const ownedCount = () => games.filter((g) => g.owned).length;

  function filteredGames() {
    const q = normalize(state.search.trim());
    let list = games.filter((game) => {
      if (state.console !== "all" && game.consoleKey !== state.console) return false;
      if (state.filter === "owned" && !game.owned) return false;
      if (state.filter === "missing" && game.owned) return false;
      if (state.filter === "favorites" && !state.favorites.has(game.id)) return false;
      if (!q) return true;
      const haystack = normalize([
        game.name, game.subtitle, game.region, game.generation,
        consoleOf(game).name, game.year, game.mascot, game.tag
      ].join(" "));
      return haystack.includes(q);
    });

    list.sort((a, b) => {
      if (state.sort === "name") return a.name.localeCompare(b.name, "es");
      if (state.sort === "generation") {
        return generationNumber(a.generation) - generationNumber(b.generation) || a.year - b.year;
      }
      return a.year - b.year || a.name.localeCompare(b.name, "es");
    });
    return list;
  }

  function renderNav() {
    el.nav.innerHTML = consoles.map((console) => {
      const list = console.key === "all" ? games : games.filter((g) => g.consoleKey === console.key);
      const count = list.length;
      const countOwned = list.filter((g) => g.owned).length;
      const active = state.console === console.key ? " active" : "";
      const small = `${countOwned} de ${count} en colección`;
      return `
        <button class="nav-item${active}" data-console="${console.key}" style="--accent:${console.color}" aria-pressed="${state.console === console.key}">
          <span class="nav-icon">${console.short}</span>
          <span class="nav-text"><strong>${escapeHtml(console.name)}</strong><small>${small}</small></span>
          <span class="nav-count">${count}</span>
        </button>`;
    }).join("");
  }

  function renderHeader() {
    const console = consoleMap[state.console] || consoles[0];
    const total = state.console === "all" ? games.length : games.filter((g) => g.consoleKey === state.console).length;
    const owned = (state.console === "all" ? games : games.filter((g) => g.consoleKey === state.console)).filter((g) => g.owned).length;
    el.title.textContent = state.console === "all" ? "Todos los juegos" : console.name;
    el.subtitle.textContent = `${total} juegos · ${owned} en tu colección · ${total - owned} por conseguir`;
    el.collectionCount.textContent = `${ownedCount()} / ${games.length}`;
    el.collectionProgress.style.width = `${(ownedCount() / games.length) * 100}%`;
    el.collectionHint.textContent = ownedCount() === games.length
      ? "¡Colección completa! Ya tienes todas las entregas."
      : `${ownedCount()} disponibles. Te faltan ${games.length - ownedCount()} juegos para completar la colección.`;
  }

  function renderChips() {
    el.filterChips.querySelectorAll(".chip").forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.filter === state.filter);
    });
  }

  function cardMarkup(game) {
    const console = consoleOf(game);
    const fav = state.favorites.has(game.id);
    const ownedBadge = game.owned
      ? '<span class="owned-badge">En colección</span>'
      : '<span class="missing-badge">Sin ROM</span>';
    return `
      <article class="game-card ${game.owned ? "owned" : "missing"}" data-id="${game.id}" tabindex="0" role="button"
        aria-label="${escapeHtml(game.name)} — ${escapeHtml(console.name)} — ${game.owned ? "en colección" : "sin ROM"}"
        style="--accent:${game.accent};--accent2:${game.accent2}">
        <div class="cover-wrap">
          <div class="cover-fallback"><span>${escapeHtml(game.mascot)}</span></div>
          <img src="${game.cover}" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer">
          ${ownedBadge}
          <span class="gen-badge">Gen ${game.generation}</span>
          <button class="fav-btn ${fav ? "is-fav" : ""}" data-fav="${game.id}" aria-label="${fav ? "Quitar de favoritos" : "Añadir a favoritos"}" title="${fav ? "Quitar de favoritos" : "Añadir a favoritos"}">♥</button>
        </div>
        <div class="card-body">
          <div class="card-meta"><span class="console-dot"></span>${console.short} · ${game.year}</div>
          <h3>${escapeHtml(game.name)}</h3>
          <p>${escapeHtml(game.region)} · ${escapeHtml(game.mascot)}</p>
          <span class="card-tag">${escapeHtml(game.tag)}</span>
        </div>
      </article>`;
  }

  function renderGrid() {
    const list = filteredGames();
    el.resultCount.textContent = `${list.length} ${list.length === 1 ? "juego" : "juegos"}`;
    el.empty.hidden = list.length > 0;
    el.grid.hidden = list.length === 0;
    el.grid.innerHTML = list.map(cardMarkup).join("");
    el.grid.querySelectorAll("img").forEach((img) => {
      img.addEventListener("error", () => {
        img.style.display = "none";
        img.closest(".cover-wrap").classList.add("no-cover");
      }, { once: true });
    });
  }

  function renderAll() {
    renderNav();
    renderHeader();
    renderChips();
    renderGrid();
  }

  function toggleFavorite(id) {
    if (state.favorites.has(id)) state.favorites.delete(id);
    else state.favorites.add(id);
    storage.set("poke-favs", JSON.stringify([...state.favorites]));
    if (state.filter === "favorites") renderGrid();
    const game = games.find((g) => g.id === id);
    const card = el.grid.querySelector(`[data-id="${id}"] .fav-btn`);
    if (card) {
      const fav = state.favorites.has(id);
      card.classList.toggle("is-fav", fav);
      card.setAttribute("aria-label", fav ? "Quitar de favoritos" : "Añadir a favoritos");
      card.title = fav ? "Quitar de favoritos" : "Añadir a favoritos";
    }
    toast(state.favorites.has(id) ? `<strong>${escapeHtml(game?.name || "Juego")}</strong> añadido a favoritos.` : `<strong>${escapeHtml(game?.name || "Juego")}</strong> quitado de favoritos.`, 2000);
  }


  const toast = window.PokeUI.toast;
  const openGame = id => {
    try { sessionStorage.setItem('poke-library-state', JSON.stringify({console:state.console, filter:state.filter, search:state.search, sort:state.sort, scroll:window.scrollY}));
    sessionStorage.setItem('poke-game-order', JSON.stringify(filteredGames().map(game=>game.id)));
    } catch { /* Navigation still works without session storage. */ }
    location.href = `/games/${encodeURIComponent(id)}`;
  };
  try {
    const saved = JSON.parse(sessionStorage.getItem('poke-library-state') || 'null');
    if (saved) {
      if (consoleMap[saved.console]) state.console = saved.console;
      if (['all','owned','favorites','missing'].includes(saved.filter)) state.filter = saved.filter;
      state.search = saved.search || '';
      if (['release','name','generation'].includes(saved.sort)) state.sort = saved.sort;
      el.search.value = state.search; el.sort.value = state.sort;
    }
  } catch { /* Ignore invalid stored preferences. */ }
  const requestedConsole = new URLSearchParams(location.search).get('console');
  if (requestedConsole && consoleMap[requestedConsole]) state.console = requestedConsole;

  // Events
  el.nav.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-console]");
    if (!btn) return;
    state.console = btn.dataset.console;
    renderAll();

  });

  el.filterChips.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-filter]");
    if (!btn) return;
    state.filter = btn.dataset.filter;
    renderChips();
    renderGrid();
  });

  let searchTimer = null;
  el.search.addEventListener("input", (event) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.search = event.target.value;
      renderGrid();
    }, 90);
  });

  el.sort.addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderGrid();
  });

  el.grid.addEventListener("click", (event) => {
    const fav = event.target.closest("[data-fav]");
    if (fav) {
      event.stopPropagation();
      toggleFavorite(fav.dataset.fav);
      return;
    }
    const card = event.target.closest("[data-id]");
    if (card) openGame(card.dataset.id);
  });

  el.grid.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const card = event.target.closest("[data-id]");
    if (!card) return;
    if (event.target.closest("[data-fav]")) return;
    event.preventDefault();
    openGame(card.dataset.id);
  });

  el.viewBtn.addEventListener("click", () => {
    state.view = state.view === "grid" ? "list" : "grid";
    document.body.classList.toggle("list-view", state.view === "list");
    el.viewBtn.classList.toggle("active", state.view === "list");
    storage.set("poke-view", state.view);
  });

  el.randomBtn.addEventListener("click", () => {
    const list = filteredGames();
    if (!list.length) return;
    openGame(list[Math.floor(Math.random() * list.length)].id);
  });

  el.clearFilters.addEventListener("click", () => {
    state.filter = "all";
    state.search = "";
    state.console = "all";
    el.search.value = "";
    renderAll();
  });


  window.addEventListener('poke-library-updated', renderAll);
  if (state.view === 'list') { document.body.classList.add('list-view'); el.viewBtn.classList.add('active'); }
  renderAll();
  try { const saved = JSON.parse(sessionStorage.getItem('poke-library-state') || 'null'); if (saved) requestAnimationFrame(()=>window.scrollTo(0,saved.scroll || 0)); } catch {}
})();
