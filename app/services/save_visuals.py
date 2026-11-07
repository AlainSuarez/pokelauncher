"""Attach existing local Pokédex images to a save response, without downloads."""
from contextlib import closing
import sqlite3
from urllib.parse import quote

from app.pokedex_catalog import GAME_PACKAGES, PACKAGES


def enrich(snapshot, game, directory):
    if not snapshot:
        return snapshot
    pokemon = (list(snapshot['party']) + [p for box in snapshot['boxes'] for p in box['pokemon']]
               + (snapshot.get('battle_box') or {}).get('pokemon', []))
    species = sorted({p['species'] for p in pokemon})
    if not species:
        return snapshot
    package = PACKAGES.get(GAME_PACKAGES.get(game), {})
    version = package.get('games', {}).get(game, '')
    assets, types = {}, {}
    database = directory / 'pokedex.sqlite3'
    if database.is_file():
        try:
            with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as db:
                db.row_factory = sqlite3.Row
                marks = ','.join('?' for _ in species)
                rows = db.execute(f'''SELECT p.id, p.artwork, s.image FROM pokemon p
                    LEFT JOIN pokemon_sprites s ON s.pokemon_id=p.id AND s.version=?
                    WHERE p.id IN ({marks})''', (version, *species)).fetchall()
                assets = {row['id']: dict(row) for row in rows}
                rows = db.execute(f'''SELECT pt.pokemon_id, t.slug, t.name FROM pokemon_types pt
                    JOIN types t ON t.slug=pt.type_slug WHERE pt.generation=?
                    AND pt.pokemon_id IN ({marks}) ORDER BY pt.slot''', (snapshot['generation'], *species)).fetchall()
                for row in rows:
                    types.setdefault(row['pokemon_id'], []).append(dict(slug=row['slug'], name=row['name']))
        except sqlite3.Error:
            pass  # A missing or incomplete image cache must not prevent save reading.

    def image(filename):
        if not filename:
            return None
        path = directory / 'images' / filename
        if path.suffix == '.png' and path.is_file() and path.resolve().is_relative_to((directory / 'images').resolve()):
            return '/pokedex-images/' + quote(filename, safe='/')
        return None

    for p in pokemon:
        asset = assets.get(p['species'], {})
        # These are species illustrations, not a promise of the saved form/shiny art.
        p['visual'] = dict(artwork=image(asset.get('artwork', f'artwork/{p["species"]}.png')),
                           sprite=image(asset.get('image')) if p['form'] == 0 and not p['is_egg'] else None,
                           types=types.get(p['species'], []) if p['form'] == 0 and not p['is_egg'] else [])
    return snapshot
