from pathlib import Path
from flask import Blueprint, abort, current_app, render_template, request, send_from_directory
from app import ROOT
from app.services.catalog import load_catalog

pages = Blueprint('pages', __name__)
# Add future game content here, with a matching games/_<section>.html template.
GAME_SECTIONS = {'resumen': 'Resumen', 'pokedex':'Pokédex', 'partidas': 'Partidas', 'configuracion': 'Configuración'}
NAMES = {'gb':'Game Boy', 'gbc':'Game Boy Color', 'gba':'Game Boy Advance', 'nds':'Nintendo DS', '3ds':'Nintendo 3DS'}


@pages.app_context_processor
def shared_context():
    config = current_app.extensions['store'].read()
    return {'catalog': load_catalog(config), 'config': config, 'system_names': NAMES}


@pages.get('/')
@pages.get('/index.html')
def library():
    return render_template('library/index.html')


@pages.get('/games/<game_id>')
def game(game_id):
    data = load_catalog(current_app.extensions['store'].read())
    game = next((item for item in data['games'] if item['id'] == game_id), None)
    if game is None:
        abort(404)
    console = next(item for item in data['consoles'] if item['key'] == game['consoleKey'])
    section = request.args.get('section', 'resumen')
    if section not in GAME_SECTIONS:
        abort(404)
    pokedex_data = None
    download = None
    if section == 'pokedex':
        from app.repositories.pokedex import PokedexStore
        selected_id = request.args.get('pokemon', type=int)
        pokedex_data = PokedexStore(current_app.config['POKEDEX_DIR']).view(
            game_id, request.args.get('q', '')[:100], request.args.get('type', '')[:30], selected_id, request.args.get('dex', '')[:40])
        if selected_id is not None and pokedex_data and not pokedex_data['selected']:
            abort(404)
        download = current_app.extensions['pokedex_downloads'].status(game_id)
    return render_template('games/detail.html', game=game, console=console, section=section,
                           game_sections=GAME_SECTIONS, pokedex=pokedex_data, download=download)


@pages.get('/settings')
def settings():
    return render_template('settings/index.html', active_system='general')


@pages.get('/settings/fragment')
def settings_fragment():
    system = request.args.get('system', 'general')
    if system not in {'general', *NAMES}:
        abort(400)
    return render_template('settings/_form.html', active_system=system)


@pages.get('/assets/<path:filename>')
def assets(filename):
    if any(part.startswith('.') for part in Path(filename).parts):
        abort(404)
    return send_from_directory(ROOT / 'assets', filename)
