"""Conservative filename matching for the bundled catalog; no ROM contents are read."""
import json
import re
import unicodedata
from pathlib import Path


def normalize_name(value):
    value = re.sub(r'\([^)]*\)|\[[^]]*\]', ' ', value)
    value = ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(c))
    value = re.sub(r'\b(pokemon|pocket|monsters|version|edition|edicion|special)\b', '', value)
    return re.sub(r'[^a-z0-9]', '', value)


def catalog(root):
    result = []
    data = json.loads((root / 'data/catalog.json').read_text())
    for game in data['games']:
        aliases = {normalize_name(game['name']), normalize_name(game['subtitle'])} - {''}
        if game['id'] == 'yellow':
            aliases.update({'yellow', 'amarillo', 'amarilla'})
        result.append({'id': game['id'], 'system': game['consoleKey'], 'aliases': aliases})
    return result


def associate(config, files, games):
    """Keep existing available selections; require exactly one unambiguous candidate."""
    added, pending = [], []
    candidates = {game['id']: [] for game in games}
    for system, paths in files.items():
        for path in paths:
            name = normalize_name(Path(path).stem)
            matches = [game for game in games if game['system'] == system and name in game['aliases']]
            if len(matches) == 1:
                candidates[matches[0]['id']].append(path)
    for game in games:
        existing = config['games'].get(game['id'])
        if existing and existing['rom'] and Path(existing['rom']).expanduser().is_file():
            continue
        paths = sorted(set(candidates[game['id']]))
        if len(paths) == 1:
            config['games'][game['id']] = {'system': game['system'], 'rom': paths[0]}
            added.append(game['id'])
        elif len(paths) > 1:
            pending.append(game['id'])
    return {'associated': added, 'ambiguous': pending}
