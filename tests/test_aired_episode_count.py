"""A season without an episode count must not crash the aired-episodes count (TypeError int + None)."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'resources/tmdbhelper/lib/items/database/itemmeta_factories/concrete_classes/tvshow.py'


def previous_season_episode_count():
    tree = ast.parse(SOURCE.read_text())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'get_previous_season_episode_count')
    ns = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), str(SOURCE), 'exec'), ns)
    return ns['get_previous_season_episode_count']


class AiredEpisodeCount(unittest.TestCase):
    def test_missing_episode_count_counts_as_zero(self):
        seasons = [{'season': 0, 'episode_count': None}, {'season': 1, 'episode_count': 8}, {'season': 2, 'episode_count': None}]
        show = SimpleNamespace(return_basemeta_db=lambda name: SimpleNamespace(cached_data=seasons))
        self.assertEqual(previous_season_episode_count()(show, 3), 8)


if __name__ == '__main__':
    unittest.main()
