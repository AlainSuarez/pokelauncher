"""Download controls and access to local encyclopedia images."""
from pathlib import Path
from flask import Blueprint, abort, current_app, jsonify, send_from_directory

pokedex = Blueprint('pokedex', __name__)


@pokedex.get('/api/pokedex/<game_id>/status')
def status(game_id):
    return jsonify(current_app.extensions['pokedex_downloads'].status(game_id))


@pokedex.post('/api/pokedex/<game_id>/download')
def download(game_id):
    try:
        return jsonify(current_app.extensions['pokedex_downloads'].start(game_id)), 202
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except OSError:
        return jsonify(error='No se pudo guardar la descarga. Comprueba el espacio y los permisos de la carpeta de datos.'), 400


@pokedex.get('/pokedex-images/<path:filename>')
def image(filename):
    if any(part.startswith('.') for part in Path(filename).parts) or Path(filename).suffix != '.png':
        abort(404)
    return send_from_directory(current_app.config['POKEDEX_DIR'] / 'images', filename)
