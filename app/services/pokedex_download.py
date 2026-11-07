"""Resumable PokéAPI downloads. Browsing never needs the network."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from urllib.error import URLError, HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from app.repositories.pokedex import PokedexStore
from app.pokedex_catalog import PACKAGES, GAME_PACKAGES, historical_types, historical_stats

SUPPORTED_GAMES = GAME_PACKAGES
API = 'https://pokeapi.co/api/v2/'


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.part')
    temporary.write_bytes(content)
    temporary.replace(path)


def resource_id(url):
    return int(url.rstrip('/').rsplit('/', 1)[-1])


def translated(entries, field, fallback=''):
    for language in ('es', 'en'):
        for entry in entries:
            if entry['language']['name'] == language and entry.get(field):
                return entry[field]
    return fallback


class CachedSource:
    def __init__(self, directory):
        self.directory = directory

    def fetch(self, url):
        for attempt in range(3):
            try:
                request = Request(url, headers={'User-Agent':'PokeLauncher/1.0 (local offline Pokedex)'})
                with urlopen(request, timeout=30) as response:
                    return response.read()
            except HTTPError as error:
                if error.code < 500 and error.code != 429:
                    raise
                if attempt == 2:
                    raise
            except (URLError, TimeoutError, OSError):
                if attempt == 2:
                    raise
            time.sleep(attempt + 1)

    def json(self, endpoint, name):
        path = self.directory / 'cache' / endpoint / f'{name}.json'
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (ValueError, OSError):
                pass
        content = self.fetch(f'{API}{endpoint}/{name}/')
        data = json.loads(content)
        atomic_write(path, content)
        return data

    def image(self, url, relative):
        if not url:
            raise ValueError('PokéAPI no ha proporcionado la imagen esperada.')
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != 'raw.githubusercontent.com' or not parsed.path.startswith('/PokeAPI/sprites/'):
            raise ValueError('La imagen no pertenece al repositorio de sprites de PokéAPI.')
        path = self.directory / 'images' / relative
        if path.exists() and path.stat().st_size > 8:
            return relative
        content = self.fetch(url)
        if not content.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('La imagen descargada no es un PNG válido.')
        atomic_write(path, content)
        return relative


def import_pokedex(directory, game_id, progress):
    settings = PACKAGES[GAME_PACKAGES[game_id]]
    source = CachedSource(directory)
    store = PokedexStore(directory)
    store.initialize()
    progress(message='Consultando las Pokédex de esta edición…')
    version = source.json('version', settings['games'][game_id])
    group = source.json('version-group', resource_id(version['version_group']['url']))
    dexes = [source.json('pokedex', slug) for slug in settings.get('pokedexes', (settings['pokedex'],))]
    generation = settings['generation']
    allowed = {resource_id(item['url']) for item in group['pokedexes']}
    if resource_id(group['generation']['url']) != generation or any(dex['id'] not in allowed for dex in dexes):
        raise ValueError('La Pokédex descargada no corresponde a esta edición.')
    # Download each species once, retaining the independent numbering of every regional dex.
    entries = list({resource_id(entry['pokemon_species']['url']): entry
                    for dex in dexes for entry in sorted(dex['pokemon_entries'], key=lambda item:item['entry_number'])}.values())
    if any(not dex['pokemon_entries'] for dex in dexes):
        raise ValueError('La Pokédex recibida está vacía.')
    progress(total=len(entries), completed=0, message='Preparando tipos de Pokémon…')
    known_types = {}
    records = []
    for index, entry in enumerate(entries):
        species_id = resource_id(entry['pokemon_species']['url'])
        progress(message=f"Descargando {entry['pokemon_species']['name'].capitalize()} · {index + 1} de {len(entries)}")
        species = source.json('pokemon-species', species_id)
        default = next(item for item in species['varieties'] if item['is_default'])
        pokemon = source.json('pokemon', resource_id(default['pokemon']['url']))
        # Past type records are valid up to their stated generation.
        types = historical_types(pokemon, generation)
        for kind in types:
            slug = kind['type']['name']
            if slug not in known_types:
                info = source.json('type', slug)
                known_types[slug] = translated(info['names'], 'name', slug.capitalize())
        sprites = pokemon['sprites']
        artwork = source.image(sprites['other']['official-artwork']['front_default'], f'artwork/{pokemon["id"]}.png')
        # Red and Blue share the same sprite resources; Yellow has its own.
        edition_sprites = {}
        for sprite_group in set(settings['sprites'].values()):
            image = sprites.get('versions', {}).get(settings['sprite_generation'], {}).get(sprite_group, {}).get('front_default')
            edition_sprites[sprite_group] = source.image(image, f'sprites/{sprite_group}/{pokemon["id"]}.png')
        records.append((entry, species, pokemon, types, artwork, edition_sprites))
        progress(completed=index + 1)
    progress(message='Guardando la Pokédex para usarla sin conexión…')
    # Publish the edition only after every resource is present. Existing editions remain intact on failure.
    with closing(store.connect()) as db, db:
        for dex in dexes:
            db.execute('INSERT INTO pokedexes VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name', (dex['id'], dex['name'], translated(dex['names'], 'name', dex['name'])))
        for slug, name in known_types.items():
            db.execute('INSERT INTO types VALUES (?,?) ON CONFLICT(slug) DO UPDATE SET name=excluded.name', (slug, name))
        for entry, species, pokemon, types, artwork, edition_sprites in records:
            db.execute('''INSERT INTO species VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                slug=excluded.slug,name=excluded.name,genus=excluded.genus,evolves_from=excluded.evolves_from''',
                (species['id'], species['name'], translated(species['names'], 'name', species['name'].capitalize()), translated(species['genera'], 'genus'), resource_id(species['evolves_from_species']['url']) if species['evolves_from_species'] else None))
            db.execute('''INSERT INTO pokemon VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                height=excluded.height,weight=excluded.weight,artwork=excluded.artwork''',
                (pokemon['id'], species['id'], pokemon['height'], pokemon['weight'], artwork))
            for stat in historical_stats(pokemon, generation):
                db.execute('INSERT OR REPLACE INTO pokemon_stats VALUES (?,?,?,?)', (pokemon['id'], generation, stat['slug'], stat['value']))
            for edition, version_name in settings['games'].items():
                db.execute('INSERT OR REPLACE INTO pokemon_sprites VALUES (?,?,?)', (pokemon['id'], version_name, edition_sprites[settings['sprites'][edition]]))
            for kind in types:
                db.execute('INSERT OR REPLACE INTO pokemon_types VALUES (?,?,?,?)', (pokemon['id'], generation, kind['slot'], kind['type']['name']))
            for description in species['flavor_text_entries']:
                language = description['language']['name']
                if description['version']['name'] in settings['games'].values() and language in {'es', 'en'}:
                    text = ' '.join(description['flavor_text'].split())
                    db.execute('INSERT OR REPLACE INTO descriptions VALUES (?,?,?,?)', (species['id'], description['version']['name'], language, text))
        for dex in dexes:
            for entry in dex['pokemon_entries']:
                db.execute('INSERT OR REPLACE INTO pokedex_entries VALUES (?,?,?)', (dex['id'], resource_id(entry['pokemon_species']['url']), entry['entry_number']))
        for edition, version_name in settings['games'].items():
            db.execute('INSERT OR REPLACE INTO game_pokedexes VALUES (?,?,?,?,?)', (edition, version_name, dexes[0]['id'], generation, datetime.now(timezone.utc).isoformat()))
    store.share_downloaded()


class DownloadManager:
    def __init__(self, directory):
        self.directory = directory
        self.lock = threading.Lock()
        self.thread = None
        self.active_game = None
        self.state = None
        PokedexStore(directory).share_downloaded()

    def _saved_state(self, game_id):
        package = GAME_PACKAGES[game_id]
        # Preserve progress recorded by the old per-game downloader.
        for key in (package, *PACKAGES[package]['games']):
            try:
                return json.loads((self.directory / 'downloads' / f'{key}.json').read_text())
            except (OSError, ValueError):
                continue
        return {'status':'empty', 'completed':0, 'total':0, 'message':''}

    def status(self, game_id):
        if game_id not in SUPPORTED_GAMES:
            return {'status':'unsupported', 'completed':0, 'total':0}
        with self.lock:
            if self.active_game == GAME_PACKAGES[game_id] and self.thread and self.thread.is_alive():
                return dict(self.state)
            state = self._saved_state(game_id)
            if PokedexStore(self.directory).details_available(game_id):
                state['status'] = 'ready'
            elif state['status'] == 'ready':
                state.update(status='partial', message='La Pokédex está disponible; faltan recursos de esta edición.')
            elif state['status'] == 'downloading':
                state.update(status='paused', message='La descarga se interrumpió. Puedes reanudarla.')
            return state

    def start(self, game_id):
        if game_id not in SUPPORTED_GAMES:
            raise ValueError('Esta edición todavía no tiene un paquete preparado.')
        with self.lock:
            if self.thread and self.thread.is_alive():
                if self.active_game != GAME_PACKAGES[game_id]:
                    raise ValueError('Ya hay una Pokédex descargándose. Espera a que termine.')
            else:
                self.active_game = GAME_PACKAGES[game_id]
                previous = self._saved_state(game_id)
                if PokedexStore(self.directory).details_available(game_id):
                    return {'status':'ready', 'completed':previous.get('total', 0), 'total':previous.get('total', 0), 'message':'Pokédex disponible sin conexión.'}
                resume = previous.get('status') in {'downloading', 'paused', 'error'}
                self.state = {'status':'downloading', 'completed':previous.get('completed', 0) if resume else 0, 'total':previous.get('total', 0) if resume else 0, 'message':'Preparando descarga…'}
                self._save()
                self.thread = threading.Thread(target=self._run, args=(game_id,), daemon=True)
                self.thread.start()
            return dict(self.state)

    def _save(self):
        path = self.directory / 'downloads' / f'{self.active_game}.json'
        atomic_write(path, json.dumps(self.state, ensure_ascii=False).encode())

    def _progress(self, **values):
        with self.lock:
            if 'completed' in values:
                values['completed'] = max(self.state['completed'], values['completed'])
            self.state.update(values)
            self._save()

    def _run(self, game_id):
        try:
            import_pokedex(self.directory, game_id, self._progress)
            self._progress(status='ready', message='Pokédex disponible sin conexión.')
        except Exception as error:
            self._progress(status='error', message=f'No se pudo completar la descarga: {error}. Lo ya descargado se conserva.')
