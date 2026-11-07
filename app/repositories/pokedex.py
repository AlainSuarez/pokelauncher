"""Shared encyclopedia storage, independent of emulator settings and save files."""
from contextlib import closing
import json
import sqlite3
from app.pokedex_catalog import PACKAGES, GAME_PACKAGES, TYPE_NAMES, STAT_LABELS, historical_types, historical_stats
import unicodedata

SCHEMA = '''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY, slug TEXT NOT NULL, name TEXT NOT NULL,
    genus TEXT NOT NULL, evolves_from INTEGER
);
CREATE TABLE IF NOT EXISTS pokemon (
    id INTEGER PRIMARY KEY, species_id INTEGER NOT NULL REFERENCES species(id),
    height INTEGER NOT NULL, weight INTEGER NOT NULL,
    artwork TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pokemon_sprites (
    pokemon_id INTEGER NOT NULL REFERENCES pokemon(id), version TEXT NOT NULL,
    image TEXT NOT NULL, PRIMARY KEY (pokemon_id, version)
);
CREATE TABLE IF NOT EXISTS types (slug TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pokemon_types (
    pokemon_id INTEGER NOT NULL REFERENCES pokemon(id), generation INTEGER NOT NULL,
    slot INTEGER NOT NULL, type_slug TEXT NOT NULL REFERENCES types(slug),
    PRIMARY KEY (pokemon_id, generation, slot)
);
CREATE TABLE IF NOT EXISTS pokemon_stats (
    pokemon_id INTEGER NOT NULL REFERENCES pokemon(id), generation INTEGER NOT NULL,
    stat TEXT NOT NULL, value INTEGER NOT NULL CHECK(value BETWEEN 1 AND 255),
    PRIMARY KEY (pokemon_id, generation, stat)
);
CREATE TABLE IF NOT EXISTS pokedexes (id INTEGER PRIMARY KEY, slug TEXT NOT NULL, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS pokedex_entries (
    pokedex_id INTEGER NOT NULL REFERENCES pokedexes(id), species_id INTEGER NOT NULL REFERENCES species(id),
    number INTEGER NOT NULL, PRIMARY KEY (pokedex_id, species_id)
);
CREATE TABLE IF NOT EXISTS descriptions (
    species_id INTEGER NOT NULL REFERENCES species(id), version TEXT NOT NULL,
    language TEXT NOT NULL, text TEXT NOT NULL, PRIMARY KEY (species_id, version, language)
);
CREATE TABLE IF NOT EXISTS game_pokedexes (
    game_id TEXT PRIMARY KEY, version TEXT NOT NULL, pokedex_id INTEGER NOT NULL REFERENCES pokedexes(id),
    generation INTEGER NOT NULL, downloaded_at TEXT NOT NULL
);
'''


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))


class PokedexStore:
    def __init__(self, directory):
        self.directory = directory
        self.path = directory / 'pokedex.sqlite3'

    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        return db

    def initialize(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db:
            db.executescript(SCHEMA)

    def share_downloaded(self):
        """Prepare other editions from cached resources without declaring their sprites complete."""
        if not self.path.exists():
            return
        self.initialize()
        with closing(self.connect()) as db, db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='game_pokedexes'").fetchone():
                return
            for package in PACKAGES.values():
                slugs = package.get('pokedexes', (package['pokedex'],))
                marks = ','.join('?' for _ in slugs)
                rows = db.execute(f'SELECT DISTINCT species_id FROM pokedex_entries WHERE pokedex_id IN (SELECT id FROM pokedexes WHERE slug IN ({marks}))', slugs).fetchall()
                for row in rows:
                    species_id = row['species_id']
                    try:
                        species = json.loads((self.directory / 'cache/pokemon-species' / f'{species_id}.json').read_text())
                        pokemon = json.loads((self.directory / 'cache/pokemon' / f'{species_id}.json').read_text())
                    except (OSError, ValueError):
                        continue
                    for stat in historical_stats(pokemon, package['generation']):
                        db.execute('INSERT OR REPLACE INTO pokemon_stats VALUES (?,?,?,?)', (pokemon['id'], package['generation'], stat['slug'], stat['value']))
                    for kind in historical_types(pokemon, package['generation']):
                        slug = kind['type']['name']
                        db.execute('INSERT OR IGNORE INTO types VALUES (?,?)', (slug, TYPE_NAMES.get(slug,slug)))
                        db.execute('INSERT OR IGNORE INTO pokemon_types VALUES (?,?,?,?)', (pokemon['id'], package['generation'], kind['slot'], slug))
                    for description in species.get('flavor_text_entries', []):
                        version = description['version']['name']
                        language = description['language']['name']
                        if version in package['games'].values() and language in {'es','en'}:
                            db.execute('INSERT OR IGNORE INTO descriptions VALUES (?,?,?,?)', (species_id, version, language, ' '.join(description['flavor_text'].split())))

    def edition(self, game_id, dex_slug=None):
        package = PACKAGES.get(GAME_PACKAGES.get(game_id))
        if not package or not self.path.exists():
            return None
        slugs = package.get('pokedexes', (package['pokedex'],))
        dex_slug = dex_slug if dex_slug in slugs else slugs[0]
        with closing(self.connect()) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='pokedexes'").fetchone():
                return None
            row = db.execute("SELECT p.id AS pokedex_id,p.name AS dex_name FROM pokedexes p WHERE p.slug=? AND EXISTS (SELECT 1 FROM pokedex_entries e WHERE e.pokedex_id=p.id)", (dex_slug,)).fetchone()
        return dict(row, dex_slug=dex_slug, dexes=[{'slug':slug, 'name':{'kalos-central':'Kalos Central','kalos-coastal':'Kalos Costa','kalos-mountain':'Kalos Montaña'}.get(slug, slug.capitalize())} for slug in slugs], game_id=game_id, version=package['games'][game_id], generation=package['generation']) if row else None

    def available(self, game_id):
        return self.edition(game_id) is not None

    def details_available(self, game_id):
        edition = self.edition(game_id)
        if not edition:
            return False
        with closing(self.connect()) as db:
            if not db.execute('SELECT 1 FROM game_pokedexes WHERE game_id=?', (game_id,)).fetchone():
                return False
            slugs = PACKAGES[GAME_PACKAGES[game_id]].get('pokedexes', (PACKAGES[GAME_PACKAGES[game_id]]['pokedex'],))
            marks = ','.join('?' for _ in slugs)
            dexes = db.execute(f'SELECT id FROM pokedexes WHERE slug IN ({marks})', slugs).fetchall()
            if len(dexes) != len(slugs):
                return False
            images = db.execute(f"SELECT sp.image FROM pokedex_entries e JOIN pokemon p ON p.species_id=e.species_id AND p.id=e.species_id LEFT JOIN pokemon_sprites sp ON sp.pokemon_id=p.id AND sp.version=? WHERE e.pokedex_id IN (SELECT id FROM pokedexes WHERE slug IN ({marks}))", (edition['version'], *slugs)).fetchall()
            return bool(images) and all(row['image'] and (self.directory / 'images' / row['image']).is_file() for row in images)

    def view(self, game_id, search='', type_slug='', selected_id=None, dex_slug=None):
        edition = self.edition(game_id, dex_slug)
        if not edition:
            return None
        with closing(self.connect()) as db:
            rows = db.execute('''SELECT s.*, p.id AS pokemon_id, p.height, p.weight, p.artwork, sp.image AS sprite, e.number
                FROM pokedex_entries e JOIN species s ON s.id=e.species_id
                JOIN pokemon p ON p.species_id=s.id AND p.id=s.id
                LEFT JOIN pokemon_sprites sp ON sp.pokemon_id=p.id AND sp.version=?
                WHERE e.pokedex_id=? ORDER BY e.number''', (edition['version'], edition['pokedex_id'])).fetchall()
            type_rows = db.execute('''SELECT pt.pokemon_id, t.slug, t.name FROM pokemon_types pt
                JOIN types t ON t.slug=pt.type_slug WHERE pt.generation=? ORDER BY pt.slot''', (edition['generation'],)).fetchall()
            by_pokemon = {}
            for row in type_rows:
                by_pokemon.setdefault(row['pokemon_id'], []).append({'slug':row['slug'], 'name':row['name']})
            all_pokemon = [dict(row, types=by_pokemon.get(row['pokemon_id'], [])) for row in rows]
            available_types = {kind['slug']:kind['name'] for pokemon in all_pokemon for kind in pokemon['types']}
            query = normalize(search.strip())
            filtered = [pokemon for pokemon in all_pokemon if
                        (not query or query in normalize(pokemon['name']) or query in pokemon['slug'] or query.lstrip('#').lstrip('0') == str(pokemon['number'])) and
                        (not type_slug or type_slug in [kind['slug'] for kind in pokemon['types']])]
            selected = next((pokemon for pokemon in all_pokemon if pokemon['id'] == selected_id), None)
            if selected:
                index = next(index for index, pokemon in enumerate(all_pokemon) if pokemon['id'] == selected_id)
                selected = dict(selected, previous=all_pokemon[index - 1] if index > 0 else None,
                                next=all_pokemon[index + 1] if index + 1 < len(all_pokemon) else None)
                texts = db.execute('SELECT language, text FROM descriptions WHERE species_id=? AND version=?', (selected['id'], edition['version'])).fetchall()
                translations = {row['language']:row['text'] for row in texts}
                language = 'es' if translations.get('es') else 'en'
                selected = dict(selected, description=translations.get(language, ''), language=language)
                stat_rows = db.execute('SELECT stat,value FROM pokemon_stats WHERE pokemon_id=? AND generation=?', (selected['pokemon_id'],edition['generation'])).fetchall()
                stat_values = {row['stat']:row['value'] for row in stat_rows}
                order = ('hp','attack','defense','special','speed') if edition['generation'] == 1 else ('hp','attack','defense','special-attack','special-defense','speed')
                selected['stats'] = [{'slug':slug,'label':STAT_LABELS[slug],'value':stat_values[slug]} for slug in order] if all(slug in stat_values for slug in order) else []
                selected['stats_total'] = sum(stat['value'] for stat in selected['stats'])
                from app.services.pokemon_profile import build_profile
                selected['profile'] = build_profile(self.directory,selected,edition,all_pokemon)
                selected['relatives'] = [pokemon for pokemon in all_pokemon if pokemon['id'] == selected['evolves_from'] or pokemon['evolves_from'] == selected['id']]
        return {'edition':edition, 'pokemon':filtered, 'total':len(all_pokemon),
                'types':sorted(available_types.items(), key=lambda pair:pair[1]),
                'selected':selected, 'search':search, 'type_slug':type_slug}
