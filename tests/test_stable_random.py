"""Random widgets keep their pick across refreshes and pages of the same day."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'resources/tmdbhelper/lib/addon/stablerandom.py'
spec = importlib.util.spec_from_file_location('stablerandom', SOURCE)
stablerandom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stablerandom)
stable_random = stablerandom.stable_random

WIDGET = 'info=random_keywords&tmdb_type=movie&sort_by=popularity.desc&reload=1792523421&widget=true'
REFRESHED = 'info=random_keywords&tmdb_type=movie&sort_by=popularity.desc&reload=1792523542&widget=true'
NEXT_PAGE = ('info=random_keywords&tmdb_type=movie&sort_by=popularity.desc&cacheonly=False'
             '&plugin_category=Dancing&page=2&reload=%24INFO%5BWindow%28Home%29.Property%28TMDbHelper.Widgets.Reload%29%5D&widget=true')
CHOICES = list(range(1000))


def pick(paramstring, day='2026-10-20'):
    return stable_random(paramstring, day=day).choice(CHOICES)


class StableRandomTest(unittest.TestCase):
    def test_refresh_keeps_pick(self):
        self.assertEqual(pick(WIDGET), pick(REFRESHED))

    def test_next_page_keeps_pick(self):
        self.assertEqual(pick(WIDGET), pick(NEXT_PAGE))
        self.assertEqual(pick(WIDGET), pick('?' + WIDGET))

    def test_other_widget_or_day_changes_pick(self):
        other = WIDGET.replace('tmdb_type=movie', 'tmdb_type=tv')
        self.assertNotEqual(pick(WIDGET), pick(other))
        self.assertNotEqual(pick(WIDGET), pick(WIDGET, day='2026-10-21'))


if __name__ == '__main__':
    unittest.main()
