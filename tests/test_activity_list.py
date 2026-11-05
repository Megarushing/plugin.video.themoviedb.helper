"""trakt_activity: latest finish or stop per title, newest first, show title over episode title."""
import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'resources/tmdbhelper/lib/sync/itemlist.py'


class Getter:
    def __init__(self, rows):
        self.rows, self.additional_keys = rows, ()

    @property
    def items(self):
        return self.rows


class SyncData:
    def __init__(self, watched, playback):
        self.watched, self.playback = watched, playback

    def get_all_watched_getter(self, item_type):
        return Getter(self.watched.get(item_type, []))

    def get_all_playback_getter(self, item_type):
        return Getter(self.playback.get(item_type, []))


def activity_class():
    tree = ast.parse(SOURCE.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ItemListSyncDataActivity')
    node.bases = [ast.Name('Base', ast.Load())]
    ns = {'Base': object}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(SOURCE), 'exec'), ns)
    return ns[node.name]


def run(watched, playback, item_types=('movie', 'show'), sort_how='desc'):
    obj = activity_class()()
    obj.syncdata, obj.item_types, obj.sort_how = SyncData(watched, playback), item_types, sort_how
    return obj.get_items()


class ActivityList(unittest.TestCase):
    def test_orders_by_latest_finish_or_stop(self):
        items = run(
            {'movie': [{'tmdb_id': 1, 'title': 'Old', 'last_watched_at': '2026-01-01'}],
             'show': [{'tmdb_id': 9, 'title': 'Show', 'last_watched_at': '2026-03-01'}]},
            {'movie': [{'tmdb_id': 2, 'title': 'Paused', 'playback_paused_at': '2026-02-01'}],
             'episode': [{'tmdb_id': 9, 'title': 'Episode 4', 'playback_paused_at': '2026-04-01'}]})
        self.assertEqual([(i['mediatype'], i['id']) for i in items], [('show', 9), ('movie', 2), ('movie', 1)])
        self.assertEqual(items[0]['title'], 'Show')

    def test_rows_without_a_date_are_skipped_and_empty_is_none(self):
        self.assertIsNone(run({'movie': [{'tmdb_id': 1, 'title': 'x', 'last_watched_at': None}]}, {}, ('movie',)))

    def test_ascending(self):
        items = run({'movie': [{'tmdb_id': 1, 'title': 'a', 'last_watched_at': '2026-01-01'},
                               {'tmdb_id': 2, 'title': 'b', 'last_watched_at': '2026-02-01'}]}, {}, ('movie',), 'asc')
        self.assertEqual([i['id'] for i in items], [1, 2])


if __name__ == '__main__':
    unittest.main()
