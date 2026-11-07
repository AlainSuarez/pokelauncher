"""Read-only bundled content, separate from user settings."""
import json
from app import ROOT


def load_catalog(config):
    data = json.loads((ROOT / 'data/catalog.json').read_text())
    from pathlib import Path
    for game in data['games']:
        entry = config['games'].get(game['id'], {})
        game['rom'] = entry.get('rom') or None
        game['owned'] = bool(game['rom']) and Path(game['rom']).expanduser().is_file()
        game['cover'] = '/' + game['cover'].lstrip('/')
    return data
