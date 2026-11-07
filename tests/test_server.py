import copy
from contextlib import closing
from types import SimpleNamespace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from app import create_app
from app.repositories.settings import DEFAULT, Store
from app.services.roms import scan
from app.services.emulators import browse_folder, browse_emulator
try:
    import flask
except ImportError:
    flask = None


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = copy.deepcopy(DEFAULT)

    def tearDown(self):
        self.temp.cleanup()

    def test_persistence_validation_scan(self):
        rom = self.root / 'Pokémon Blue (USA).gb'
        rom.write_bytes(b'fixture')
        (self.root / 'not-a-rom.txt').touch()
        self.config['systems']['gb']['folders'] = [str(self.root)]
        store = Store(self.root / 'settings.sqlite3')
        store.write(self.config)
        self.assertEqual(store.read(), self.config)
        self.assertEqual(scan(self.config)['files']['gb'], [str(rom)])
        self.config['systems']['gb']['folders'] = [str(self.root / 'missing')]
        with self.assertRaises(ValueError):
            store.write(self.config)
        self.assertNotEqual(store.read(), self.config)

    def test_native_folder_selection_and_cancel(self):
        result = MagicMock(returncode=0, stdout=str(self.root) + '\n')
        with patch('app.services.emulators.shutil.which', return_value='/usr/bin/zenity'), patch('app.services.emulators.subprocess.run', return_value=result) as run:
            self.assertEqual(browse_folder(), {'path': str(self.root)})
            self.assertIn('--directory', run.call_args.args[0])
            result.returncode = 1
            self.assertEqual(browse_folder(), {'path': None})
        with patch('app.services.emulators.shutil.which', return_value=None):
            with self.assertRaises(ValueError):
                browse_folder()

    def test_emulator_file_selection(self):
        executable = self.root / 'My Emulator.AppImage'
        executable.touch()
        executable.chmod(0o755)
        result = MagicMock(returncode=0, stdout=str(executable) + '\n')
        with patch('app.services.emulators.shutil.which', return_value='/usr/bin/zenity'), patch('app.services.emulators.subprocess.run', return_value=result) as run:
            self.assertEqual(browse_emulator()['path'], str(executable))
            self.assertNotIn('--directory', run.call_args.args[0])
            executable.chmod(0o644)
            with self.assertRaises(ValueError):
                browse_emulator()
            result.returncode = 1
            self.assertIsNone(browse_emulator()['path'])

    def test_general_root_and_console_override(self):
        for system, ext in [('gb', '.gb'), ('gba', '.gba')]:
            folder = self.root / system
            folder.mkdir()
            (folder / ('game' + ext)).touch()
        self.config['rom_root'] = str(self.root)
        result = scan(self.config)
        self.assertEqual(len(result['files']['gb']), 1)
        self.assertEqual(len(result['files']['gba']), 1)
        alternate = self.root / 'alternate'
        alternate.mkdir()
        self.config['systems']['gb']['folders'] = [str(alternate)]
        self.assertEqual(scan(self.config)['files']['gb'], [])
        store = Store(self.root / 'config.sqlite3')
        store.write(self.config)
        self.assertEqual(store.read()['rom_root'], str(self.root))
        # Existing settings retain associations and specific folders.
        import sqlite3
        legacy = copy.deepcopy(self.config)
        del legacy['rom_root']
        with closing(sqlite3.connect(store.path)) as db, db:
            db.execute('UPDATE settings SET value=?', (json.dumps(legacy),))
        self.assertEqual(store.read()['rom_root'], '')
        self.assertEqual(store.read()['systems'], legacy['systems'])

    @unittest.skipUnless(flask, "Flask is not installed")
    def test_http_security_and_launch(self):
        app = create_app(self.root / 'settings.sqlite3', testing=True)
        client = app.test_client()
        server = SimpleNamespace(token=app.extensions['token'], store=app.extensions['store'])
        origin = 'http://127.0.0.1:8765'
        def request(method, path, data=None, headers=None):
            response = client.open(path, method=method, json=data, base_url=origin, headers=headers or {})
            return response.status_code, response.get_json()
        def post(path, data, headers):
            return request('POST', path, data, headers)
        headers = {'Origin': origin, 'X-Poke-Token': server.token}
        status, _ = post('/api/config', self.config, {})
        self.assertEqual(status, 403)
        status, _ = post('/api/config', self.config, {**headers, 'Origin': 'https://example.com'})
        self.assertEqual(status, 403)
        for path in ['/server.py', '/.aws/credentials', '/data/../server.py']:
            self.assertEqual(request('GET', path)[0], 404)
        folder = self.root / 'gb'
        folder.mkdir()
        detected = folder / 'Pokemon - Blue Version (USA, Europe).gb'
        detected.touch()
        self.config['rom_root'] = str(self.root)
        self.assertEqual(post('/api/config', self.config, headers)[0], 200)
        status, result = post('/api/scan', {}, headers)
        self.assertEqual(status, 200)
        self.assertIn('blue', result['associated'])
        status, state = request('GET', '/api/state')
        self.assertEqual(status, 200)
        self.assertTrue(state['available']['blue'])
        self.assertEqual(state['config']['games']['blue']['rom'], str(detected))
        # The persisted association survives a new Store instance.
        self.assertEqual(Store(server.store.path).read()['games']['blue']['rom'], str(detected))
        rom = self.root / 'ROM with spaces.gb'
        rom.touch()
        self.config['games']['blue'] = {'rom': str(rom), 'system': 'gb'}
        self.config['systems']['gb']['emulator'] = '/test/emulator'
        self.assertEqual(post('/api/config', self.config, headers)[0], 200)
        process = MagicMock()
        process.poll.return_value = None
        with patch('app.services.emulators.shutil.which', return_value='/test/emulator'), patch('app.api.subprocess.Popen', return_value=process) as launch:
            self.assertEqual(post('/api/play', {'game': 'blue'}, headers)[0], 200)
            self.assertEqual(launch.call_args.args[0], ['/test/emulator', str(rom)])
            self.assertEqual(post('/api/play', {'game': 'blue'}, headers)[0], 400)
        rom.unlink()
        self.assertEqual(post('/api/play', {'game': 'blue'}, headers)[0], 400)


if __name__ == '__main__':
    unittest.main()
