"""Locate Azahar saves by known layout; never modify emulator files."""
import configparser
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sys

# Pokémon title IDs, independent of language; PKHeX verifies the copy on read.
TITLE_IDS = {
    'x': '00055d00', 'y': '00055e00', 'omegaruby': '0011c400',
    'alphasapphire': '0011c500', 'sun': '00164800', 'moon': '00175e00',
    'ultrasun': '001b5000', 'ultramoon': '001b5100',
}


def sdmc_directory(data, configuration):
    """Honor plain absolute Qt INI storage overrides; otherwise use the default."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        with configuration.open(encoding='utf-8-sig') as source:
            parser.read_file(source)
        for section in ('Data Storage', 'Data%20Storage'):
            if not parser.has_section(section):
                continue
            if parser.get(section, 'use_custom_storage', fallback='false').lower() != 'true':
                break
            value = parser.get(section, 'sdmc_directory', fallback='').strip().strip('"')
            if value and Path(value).is_absolute():
                return Path(value)
    except (OSError, UnicodeError, configparser.Error):
        pass
    return data / 'sdmc'


def azahar_locations(system):
    if sys.platform != 'linux' or 'azahar' not in system['emulator'].lower():
        return []
    home = Path.home()
    data = Path(os.environ.get('XDG_DATA_HOME') or home / '.local/share') / 'azahar-emu'
    config = Path(os.environ.get('XDG_CONFIG_HOME') or home / '.config') / 'azahar-emu'
    profiles = [(data, config / 'qt-config.ini', 'Azahar · nativo')]
    app_ids = {'org.azahar_emu.Azahar', 'io.github.azahar.Azahar'}
    if system['mode'] == 'flatpak' and re.fullmatch(r'[A-Za-z0-9_.-]+', system['emulator']):
        app_ids.add(system['emulator'])
    for app_id in sorted(app_ids):
        base = home / '.var/app' / app_id
        profiles.append((base / 'data/azahar-emu', base / 'config/azahar-emu/qt-config.ini', f'Azahar · Flatpak ({app_id})'))
    # Linux portable mode uses ./user relative to the emulator's working directory.
    # The launcher inherits its own working directory when launching the emulator.
    portable = Path.cwd() / 'user'
    if portable.is_dir():
        profiles.append((portable, portable / 'config/qt-config.ini', 'Azahar · portable'))
    return [(sdmc_directory(data, config), label) for data, config, label in profiles]


def discover(game, system):
    title = TITLE_IDS.get(game)
    if not title:
        return []
    found = {}
    roots = azahar_locations(system)
    # Also support a manually selected Azahar user, SDMC or title directory.
    if system['save_folder']:
        root = Path(system['save_folder']).expanduser()
        roots.extend((root / suffix, 'Carpeta configurada') for suffix in ('', 'sdmc'))
    for root, label in roots:
        for pattern in (
            f'Nintendo 3DS/*/*/title/00040000/{title}/data/00000001/main',
            f'{title}/data/00000001/main',
        ):
            try:
                for path in root.glob(pattern):
                    if not path.is_file():
                        continue
                    resolved = path.resolve()
                    stat = resolved.stat()
                    found.setdefault(str(resolved), dict(path=str(resolved), origin=label,
                        modified_at=datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()))
                    if len(found) >= 200:
                        return sorted(found.values(), key=lambda item: item['path'])
            except OSError:
                continue
    return sorted(found.values(), key=lambda item: item['path'])
