"""Application factory for the local desktop launcher."""
import os
from pathlib import Path
import secrets


from app.repositories.settings import Store

ROOT = Path(__file__).resolve().parent.parent


def create_app(database=None, *, port=8765, testing=False):
    from flask import Flask, jsonify, request
    from werkzeug.exceptions import HTTPException

    app = Flask(__name__)
    app.config.update(TESTING=testing, MAX_CONTENT_LENGTH=262144, TEMPLATES_AUTO_RELOAD=True)
    directory = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'pokelauncher'
    app.extensions['store'] = Store(Path(database) if database else directory / 'settings.sqlite3')
    from app.services.pokedex_download import DownloadManager
    app.config['POKEDEX_DIR'] = app.extensions['store'].path.parent / 'pokedex'
    app.extensions['pokedex_downloads'] = DownloadManager(app.config['POKEDEX_DIR'])
    app.extensions['token'] = secrets.token_urlsafe(32)
    app.extensions['processes'] = {}
    import threading
    app.extensions['launch_lock'] = threading.Lock()
    app.extensions['save_lock'] = threading.Lock()

    @app.before_request
    def protect_local_access():
        if request.host not in {f'127.0.0.1:{port}', f'localhost:{port}'}:
            return jsonify(error='Host no permitido.'), 403
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origins = {f'http://127.0.0.1:{port}', f'http://localhost:{port}'}
            if request.headers.get('Origin') not in origins or not secrets.compare_digest(request.headers.get('X-Poke-Token', '').encode(), app.extensions['token'].encode()):
                return jsonify(error='Solicitud no autorizada.'), 403

    @app.after_request
    def response_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    from app.api import api
    from app.pages import pages
    app.register_blueprint(api)
    app.register_blueprint(pages)
    from app.pokedex import pokedex
    app.register_blueprint(pokedex)
    from app.saves import saves
    app.register_blueprint(saves)
    return app
