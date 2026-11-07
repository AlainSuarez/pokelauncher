"""Local PokéLauncher entry point. Run: python server.py."""
import argparse
import os
from pathlib import Path

from waitress import serve
from app import create_app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev', action='store_true', help='Recargar automáticamente al cambiar archivos Python.')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'pokelauncher')
    args = parser.parse_args()
    app = create_app(args.data_dir / 'settings.sqlite3', port=args.port)
    print(f'PokéLauncher: http://127.0.0.1:{args.port}', flush=True)
    if args.dev:
        app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=True, use_debugger=False)
    else:
        serve(app, host='127.0.0.1', port=args.port, threads=8, max_request_body_size=262144)
