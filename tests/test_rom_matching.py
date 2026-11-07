import copy
from pathlib import Path
import tempfile
import unittest
from rom_matching import catalog, associate
from app.repositories.settings import DEFAULT

ROOT = Path(__file__).resolve().parents[1]


class MatchingTests(unittest.TestCase):
    def test_catalog_and_common_names(self):
        games = catalog(ROOT)
        self.assertEqual(len(games), 28)
        cases = {
            'blue': ('gb', 'Pokemon - Blue Version (USA, Europe) (SGB Enhanced).gb'),
            'black': ('nds', 'Pokemon - Black Version (USA, Europe) (NDSi Enhanced).nds'),
            'black2': ('nds', 'Pokemon - Black Version 2 (USA, Europe).nds'),
            'ultrasun': ('3ds', 'Pokemon Ultra Sun (USA).3ds'),
            'sun': ('3ds', 'Pokemon Sun (USA).cci'),
            'ruby': ('gba', 'Pokémon Edición Rubí.gba'),
            'omegaruby': ('3ds', 'Pokemon Omega Ruby (USA).3ds'),
            'yellow': ('gb', 'Pokemon - Yellow Version (USA).gb'),
        }
        config = copy.deepcopy(DEFAULT)
        files = {key: [] for key in config['systems']}
        for system, name in cases.values():
            files[system].append('/roms/' + name)
        result = associate(config, files, games)
        self.assertEqual(set(result['associated']), set(cases))
        self.assertNotIn('white', config['games'])

    def test_ambiguous_hacks_and_existing_selection(self):
        config = copy.deepcopy(DEFAULT)
        files = {'gb': ['/roms/Pokemon Blue (USA).gb', '/roms/Pokemon Blue (Europe).gb', '/roms/Pokemon Red Radical Hack.gb']}
        result = associate(config, files, catalog(ROOT))
        self.assertEqual(result['ambiguous'], ['blue'])
        self.assertFalse(config['games'])
        with tempfile.TemporaryDirectory() as directory:
            manual = Path(directory) / 'custom.gb'
            manual.touch()
            config['games']['blue'] = {'rom': str(manual), 'system': 'gb'}
            associate(config, {'gb': ['/roms/Pokemon Blue.gb']}, catalog(ROOT))
            self.assertEqual(config['games']['blue']['rom'], str(manual))
