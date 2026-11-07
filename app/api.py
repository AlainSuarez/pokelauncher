"""JSON endpoints for local files, settings and emulator processes."""
from pathlib import Path
import subprocess
import threading

from flask import Blueprint, current_app, jsonify, request

from app import ROOT
from app.repositories.settings import SYSTEMS
from app.services.emulators import browse_emulator, browse_folder, emulator_command
from app.services.roms import scan
from rom_matching import associate, catalog

api = Blueprint('api', __name__, url_prefix='/api')


@api.get('/state')
def state():
    config = current_app.extensions['store'].read()
    available = {key: bool(value['rom']) and Path(value['rom']).expanduser().is_file() for key, value in config['games'].items()}
    return jsonify(config=config, available=available, token=current_app.extensions['token'], capabilities=['auto-associate-v1'])


@api.post('/<action>')
def action(action):
    if action not in {'browse-emulator', 'browse-folder', 'config', 'scan', 'check', 'play'}:
        return jsonify(error='Ruta inexistente.'), 404
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            raise ValueError('Se esperaba un objeto JSON.')
        store = current_app.extensions['store']
        if action == 'browse-emulator':
            return jsonify(browse_emulator())
        if action == 'browse-folder':
            return jsonify(browse_folder())
        if action == 'config':
            store.write(data)
            return jsonify(ok=True)
        config = store.read()
        if action == 'scan':
            result = scan(config)
            result.update(associate(config, result['files'], catalog(ROOT)))
            store.write(config)
            return jsonify(result)
        if action == 'check':
            return jsonify(message='Emulador encontrado.', command=emulator_command(config['systems'][data['system']]))
        with current_app.extensions['launch_lock']:
            game_id = data['game']
            association = config['games'].get(game_id)
            if not association:
                raise ValueError('Asocia primero una ROM a este juego en Configuración.')
            rom = Path(association['rom']).expanduser().resolve()
            if not rom.is_file() or rom.suffix.lower() not in SYSTEMS[association['system']]:
                raise ValueError('La ROM no existe o su extensión no es compatible.')
            processes = current_app.extensions['processes']
            process = processes.get(game_id)
            if process and process.poll() is None:
                raise ValueError('Este juego ya tiene una sesión abierta desde el launcher.')
            command = emulator_command(config['systems'][association['system']])
            process = subprocess.Popen([*command, str(rom)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            processes[game_id] = process
            threading.Thread(target=process.wait, daemon=True).start()
        return jsonify(message='Solicitud de apertura enviada al emulador.')
    except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError) as error:
        return jsonify(error=str(error)), 400
