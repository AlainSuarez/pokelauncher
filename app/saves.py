"""Local save selection and explicit read requests, protected by the app token."""
from flask import Blueprint, current_app, jsonify, request

from app.services.catalog import load_catalog
from app.services.saves import read_save, status
from app.services.save_visuals import enrich

saves = Blueprint('saves', __name__)


@saves.route('/api/saves/<game_id>', methods=['GET', 'POST'])
def game_save(game_id):
    store = current_app.extensions['store']
    config = store.read()
    game = next((game for game in load_catalog(config)['games'] if game['id'] == game_id), None)
    if game is None:
        return jsonify(error='Juego inexistente.'), 404
    try:
        if request.method == 'GET':
            result = status(store.path, game_id, config, game['consoleKey'])
            enrich(result['snapshot'], game_id, current_app.config['POKEDEX_DIR'])
            return jsonify(result)
        data = request.get_json()
        if not isinstance(data, dict):
            raise ValueError('Se esperaba un objeto JSON.')
        with current_app.extensions['save_lock']:
            result = read_save(data.get('path'), game_id, store.path)
        enrich(result, game_id, current_app.config['POKEDEX_DIR'])
        return jsonify(result)
    except (ValueError, OSError) as error:
        return jsonify(error=str(error)), 400
