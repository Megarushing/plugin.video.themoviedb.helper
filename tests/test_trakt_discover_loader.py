"""Exercise the real Trakt editor loader without requiring Kodi's GUI modules."""
import ast
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import Any
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'resources/tmdbhelper/lib/script/discover/trakt.py'


def loader_class() -> Any:
    tree = ast.parse(SOURCE.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TraktDiscoverMain')
    cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'load_values']
    cls.decorator_list = []
    class Base:
        def load_values(self, **kwargs):
            self.loaded = kwargs
    ns = {'DiscoverMain': Base}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), str(SOURCE), 'exec'), ns)
    return ns['TraktDiscoverMain']


class TraktDiscoverLoader(unittest.TestCase):
    def load(self, saved, **kwargs):
        editor = loader_class()()
        types = []
        editor.routes_dict = {'tmdb_type': SimpleNamespace(load_value=types.append)}
        editor.winprop = 'TraktDiscover.Path'
        package = ModuleType('jurialmunkey')
        package.__path__ = []
        window = ModuleType('jurialmunkey.window')
        setattr(window, 'get_property', lambda key: saved if key == 'TraktDiscover.Path.paramstring' else '')
        with patch.dict(sys.modules, {'jurialmunkey': package, 'jurialmunkey.window': window}):
            editor.load_values(**kwargs)
        return types, editor.loaded

    def test_opt_in_restores_route_as_list_and_all_filters(self):
        types, values = self.load('info=trakt_popular&tmdb_type=tv&years=2020-2026&genres=crime&query=Slow+Horses',
                                  use_winprops='true', info='trakt_discover')
        self.assertEqual(types, ['tv'])

        self.assertEqual(values['list'], 'trakt_popular')
        self.assertEqual(values['query'], 'Slow Horses')
        self.assertEqual(values['genres'], 'crime')
        self.assertEqual(values['years'], '2020-2026')
        self.assertEqual(values['info'], 'trakt_discover')

    def test_opt_in_empty_property_retains_defaults(self):
        types, values = self.load('', use_winprops='true')
        self.assertEqual(types, ['movie'])

    def test_ordinary_call_ignores_saved_ui_state(self):
        types, values = self.load('info=trakt_popular&tmdb_type=tv', tmdb_type='movie', list='trakt_anticipated')
        self.assertEqual(types, ['movie'])
        self.assertEqual(values['list'], 'trakt_anticipated')


if __name__ == '__main__':
    unittest.main()
