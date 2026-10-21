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


class RandomListSlotsTest(unittest.TestCase):
    def setUp(self):
        self.items = [{'params': {'user_slug': 'owner', 'list_slug': str(i)}} for i in range(8)]
        self.base = 'info=random_likedlists&tmdb_type=both&hub=123'

    def choose(self, slot, items=None, suffix='', day='2026-10-21'):
        return stablerandom.stable_list_choice(
            self.base + '&random_slot=' + str(slot) + suffix,
            self.items if items is None else items, day=day)['params']['list_slug']

    def test_three_slots_are_distinct(self):
        self.assertEqual(len({self.choose(i) for i in (1, 2, 3)}), 3)

    def test_each_slot_survives_refresh_pagination_and_pool_reordering(self):
        for slot in (1, 2, 3):
            self.assertEqual(self.choose(slot), self.choose(
                slot, list(reversed(self.items)), '&page=3&reload=99&plugin_category=Title&widget=true'))

    def test_duplicate_pool_entries_cannot_duplicate_slots(self):
        pool = self.items + self.items
        self.assertEqual(len({self.choose(i, pool) for i in (1, 2, 3)}), 3)

    def test_small_pool_cycles_without_error(self):
        self.assertEqual(self.choose(1, self.items[:1]), self.choose(3, self.items[:1]))

    def test_no_slot_preserves_existing_selection(self):
        expected = stable_random(self.base, day='2026-10-21').choice(self.items)
        self.assertEqual(stablerandom.stable_list_choice(self.base, self.items, day='2026-10-21'), expected)

    def test_bad_slot_falls_back_to_legacy(self):
        for slot in ('bad', '0', '-1'):
            self.assertEqual(self.choose(slot), stablerandom.stable_list_choice(
                self.base, self.items, day='2026-10-21')['params']['list_slug'])


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
