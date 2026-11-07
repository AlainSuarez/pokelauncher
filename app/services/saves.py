"""Read-only PKHeX bridge. The helper never receives the original save path."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time

from app import ROOT

MAX_SIZE = 16 * 1024 * 1024
HELPER = ROOT / 'tools/SaveReader/publish/SaveReader.dll'
VERSIONS = {
    'red': {'RD', 'RB'}, 'blue': {'GN', 'BU', 'RB'}, 'yellow': {'YW'},
    'gold': {'GD', 'GS'}, 'silver': {'SI', 'GS'}, 'crystal': {'C'},
    'ruby': {'R', 'RS'}, 'sapphire': {'S', 'RS'}, 'emerald': {'E'},
    'firered': {'FR', 'FRLG'}, 'leafgreen': {'LG', 'FRLG'},
    'diamond': {'D'}, 'pearl': {'P'}, 'platinum': {'Pt'},
    'heartgold': {'HG'}, 'soulsilver': {'SS'}, 'black': {'B'}, 'white': {'W'},
    'black2': {'B2'}, 'white2': {'W2'}, 'x': {'X'}, 'y': {'Y'},
    'omegaruby': {'OR'}, 'alphasapphire': {'AS'}, 'sun': {'SN'}, 'moon': {'MN'},
    'ultrasun': {'US'}, 'ultramoon': {'UM'},
}


def association(database, game, path=None):
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS save_associations (game TEXT PRIMARY KEY, path TEXT NOT NULL)')
        if path is not None:
            db.execute('INSERT OR REPLACE INTO save_associations VALUES (?, ?)', (game, str(path)))
        row = db.execute('SELECT path FROM save_associations WHERE game=?', (game,)).fetchone()
        return row[0] if row else ''


def cached_snapshot(database, game):
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS save_snapshots (game TEXT PRIMARY KEY, content BLOB NOT NULL, payload TEXT NOT NULL)')
        row = db.execute('SELECT content,payload FROM save_snapshots WHERE game=?', (game,)).fetchone()
    if not row:
        return None
    content, previous = row
    result = json.loads(previous)
    # Upgrade the interpretation of an existing copy, not its saved game state.
    # No access to the emulator's original is needed, including after a restart.
    outdated = game in {'x', 'y'} and ('storage' not in result or 'battle_box' not in result)
    if not outdated or not shutil.which('dotnet') or not HELPER.is_file():
        return result
    try:
        if hashlib.sha256(content).hexdigest() != result['source']['sha256']:
            raise ValueError('La copia almacenada no supera la comprobación de integridad.')
        with tempfile.TemporaryDirectory(prefix='pokelauncher-cached-') as directory:
            copy = Path(directory) / (Path(result['source']['path']).name or 'main')
            copy.write_bytes(content)
            updated = decode(copy, game)
        if 'storage' not in updated or 'battle_box' not in updated:
            raise ValueError('El lector necesita actualizarse para mostrar todas las cajas.')
        updated['source'] = result['source']
        updated['edition_ambiguous'] = result.get('edition_ambiguous', False)
        with closing(sqlite3.connect(database)) as db, db:
            # Do not replace a newer snapshot if another request refreshed it.
            db.execute('UPDATE save_snapshots SET payload=? WHERE game=? AND payload=?',
                       (json.dumps(updated), game, previous))
            latest = db.execute('SELECT payload FROM save_snapshots WHERE game=?', (game,)).fetchone()
        return json.loads(latest[0]) if latest else updated
    except (ValueError, OSError):
        result['reader_refresh_error'] = True
        return result


def status(database, game, config, system):
    from app.services.save_discovery import discover
    detected = discover(game, config['systems'][system])
    folder = config['systems'][system]['save_folder']
    candidates = []
    truncated = False
    if folder and Path(folder).expanduser().is_dir():
        # No recursive traversal: emulator directories can contain very large trees.
        for path in Path(folder).expanduser().iterdir():
            if path.is_file() and (path.suffix.lower() in {'.sav', '.srm', '.dsv', '.dat', '.bin'} or path.name == 'main'):
                candidates.append(str(path))
                if len(candidates) == 200:
                    truncated = True
                    break
    from rom_matching import catalog, normalize_name
    aliases = next((entry['aliases'] for entry in catalog(ROOT) if entry['id'] == game), set())
    rom = config['games'].get(game, {}).get('rom', '')
    if rom:
        aliases = aliases | {normalize_name(Path(rom).stem)}
    selected = association(database, game)
    known = {item['path'] for item in detected}
    for candidate in candidates + ([selected] if selected else []):
        path = Path(candidate).expanduser()
        if not path.is_file() or (candidate != selected and normalize_name(path.stem) not in aliases):
            continue
        resolved = str(path.resolve())
        if resolved not in known:
            detected.append(dict(path=resolved, origin='Carpeta configurada',
                                 modified_at=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()))
            known.add(resolved)
    return dict(ready=bool(shutil.which('dotnet') and HELPER.is_file()),
                path=association(database, game), folder=folder, candidates=sorted(candidates), truncated=truncated,
                snapshot=cached_snapshot(database, game), detected=detected)


class SnapshotBusy(ValueError):
    """The source may be in the middle of an emulator save."""


def capture(path):
    # Validate only the copying interval. Later emulator saves are independent.
    try:
        before = path.stat()
        if not path.is_file():
            raise ValueError('La ruta no corresponde a un archivo normal.')
        if not 0 < before.st_size <= MAX_SIZE:
            raise SnapshotBusy('Tamaño de partida no admitido (máximo 16 MiB).')
        with path.open('rb') as source:
            content = source.read(MAX_SIZE + 1)
        with path.open('rb') as source:
            verification = source.read(MAX_SIZE + 1)
        after = path.stat()
    except FileNotFoundError as error:
        raise SnapshotBusy('La partida no está disponible en este momento.') from error
    fingerprint = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if len(content) != before.st_size or content != verification or fingerprint(before) != fingerprint(after):
        raise SnapshotBusy('La partida sigue cambiando mientras se copia.')
    return content, before


def decode(snapshot, game):
    try:
        process = subprocess.run(['dotnet', str(HELPER), str(snapshot)], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as error:
        raise ValueError('El lector tardó demasiado en responder.') from error
    try:
        result = json.loads(process.stdout)
    except (ValueError, TypeError) as error:
        raise ValueError('El lector no devolvió una respuesta válida. Comprueba su instalación.') from error
    if not isinstance(result, dict) or result.get('schema_version') != 1:
        raise ValueError('Versión de respuesta del lector no compatible.')
    if process.returncode or result.get('error'):
        raise SnapshotBusy(result.get('error') or 'No se pudo leer la copia de la partida.')
    if result.get('version') not in VERSIONS.get(game, set()):
        raise ValueError(f"La edición detectada ({result.get('version', '?')}) no corresponde a este juego.")
    return result


def read_save(raw_path, game, database):
    if not isinstance(raw_path, str) or not raw_path.strip() or '\0' in raw_path or len(raw_path) >= 4096:
        raise ValueError('Indica la ruta completa de una partida.')
    if not shutil.which('dotnet') or not HELPER.is_file():
        raise ValueError('El lector PKHeX.Core no está preparado. Consulta la instalación del lector en README.md.')
    path = Path(raw_path).expanduser().resolve()
    for attempt in range(3):
        try:
            content, metadata = capture(path)
            with tempfile.TemporaryDirectory(prefix='pokelauncher-save-') as directory:
                snapshot = Path(directory) / path.name
                snapshot.write_bytes(content)
                result = decode(snapshot, game)
            break
        except SnapshotBusy as error:
            if attempt == 2:
                raise ValueError(f'No se pudo obtener una copia válida tras 3 intentos. {error} Se conserva la última lectura válida.') from error
            time.sleep(2)
    result['source'] = dict(path=str(path), sha256=hashlib.sha256(content).hexdigest(),
                            modified_at=datetime.fromtimestamp(metadata.st_mtime, timezone.utc).isoformat(),
                            read_at=datetime.now(timezone.utc).isoformat())
    result['edition_ambiguous'] = result['version'] in {'RB', 'GS', 'RS', 'FRLG'}
    # Replace the bytes, displayed data and association together, only on success.
    # SQLite lives in the launcher's data directory, never in the emulator folder.
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS save_snapshots (game TEXT PRIMARY KEY, content BLOB NOT NULL, payload TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS save_associations (game TEXT PRIMARY KEY, path TEXT NOT NULL)')
        db.execute('INSERT OR REPLACE INTO save_snapshots VALUES (?, ?, ?)', (game, content, json.dumps(result)))
        db.execute('INSERT OR REPLACE INTO save_associations VALUES (?, ?)', (game, str(path)))
    return result
