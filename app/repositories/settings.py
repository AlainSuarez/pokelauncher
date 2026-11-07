from contextlib import closing
import json
from pathlib import Path
import sqlite3

SYSTEMS = {'gb': ('.gb', '.gbc'), 'gbc': ('.gbc', '.gb'), 'gba': ('.gba',), 'nds': ('.nds',), '3ds': ('.3ds', '.cci', '.cxi')}
DEFAULT = {'rom_root': '', 'systems': {key: {'folders': [], 'emulator': '', 'mode': 'native', 'save_folder': ''} for key in SYSTEMS}, 'games': {}}


class Store:
    def __init__(self, path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
            db.execute('PRAGMA user_version = 1')

    def read(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            row = db.execute('SELECT value FROM settings WHERE id=1').fetchone()
        data = json.loads(row[0]) if row else json.loads(json.dumps(DEFAULT))
        data.setdefault('rom_root', '')  # Preserve configurations saved before the general root.
        return data

    def write(self, data):
        if not isinstance(data, dict) or set(data) != {'rom_root', 'systems', 'games'} or not isinstance(data['games'], dict):
            raise ValueError('Configuración inválida.')
        root = data['rom_root']
        if not isinstance(root, str) or '\0' in root or len(root) >= 4096:
            raise ValueError('Carpeta raíz inválida.')
        if root and not Path(root).expanduser().is_dir():
            raise ValueError(f'La carpeta raíz no existe: {root}')
        if not isinstance(data['systems'], dict) or set(data['systems']) != set(SYSTEMS):
            raise ValueError('Consolas inválidas.')
        for system in data['systems'].values():
            if not isinstance(system, dict) or set(system) != {'folders', 'emulator', 'mode', 'save_folder'}:
                raise ValueError('Configuración de consola inválida.')
            if system['mode'] not in ('native', 'flatpak') or not isinstance(system['folders'], list):
                raise ValueError('Modo o carpetas inválidos.')
            values = system['folders'] + [system['emulator'], system['save_folder']]
            if not all(isinstance(v, str) and '\0' not in v and len(v) < 4096 for v in values):
                raise ValueError('Ruta inválida.')
            for folder in system['folders'] + [system['save_folder']]:
                if folder and not Path(folder).expanduser().is_dir():
                    raise ValueError(f'La carpeta no existe: {folder}')
        for key, value in data['games'].items():
            if not isinstance(key, str) or not isinstance(value, dict) or set(value) != {'rom', 'system'}:
                raise ValueError('Asociación de juego inválida.')
            if value['system'] not in SYSTEMS or not isinstance(value['rom'], str) or '\0' in value['rom']:
                raise ValueError('Asociación de ROM inválida.')
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('INSERT OR REPLACE INTO settings VALUES (1, ?)', (json.dumps(data),))

