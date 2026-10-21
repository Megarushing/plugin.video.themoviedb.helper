"""Exercise the real random-list wrapper without requiring a Kodi runtime."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'resources/tmdbhelper/lib/items/directories/trakt/lists_random.py'


class CustomList:
    def get_items(self, **kwargs):
        # Capture the arguments handed to the normal paginated list implementation.
        return kwargs


class SampleLists:
    params = {'info': 'trakt_userlist', 'tmdb_type': 'both',
              'list_slug': 'mindfuck', 'user_slug': 'lish408'}

    def __init__(self, *args):
        pass

    def get_items(self, **kwargs):
        return [{'params': dict(self.params)}]


class FixedChoice:
    def choice(self, items):
        return items[0]


def make_wrapper():
    tree = ast.parse(SOURCE.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                and n.name == 'ListTraktStaticTrendingRandomised')
    namespace = {'ListTraktCustom': CustomList, 'ListTraktStaticTrending': SampleLists,
                 'stable_random': lambda _: FixedChoice()}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    wrapper = namespace[node.name]()
    wrapper.paramstring = 'info=random_likedlists&page=2'
    return wrapper


class RandomListPaginationTest(unittest.TestCase):
    def test_requested_page_reaches_selected_list(self):
        for page in (1, 2, 3):
            with self.subTest(page=page):
                result = make_wrapper().get_items(info='random_likedlists', tmdb_type='both', page=page)
                self.assertEqual(result.get('page'), page)
                self.assertEqual(result['list_slug'], 'mindfuck')

    def test_selected_list_identity_wins_and_options_survive(self):
        result = make_wrapper().get_items(
            info='random_likedlists', tmdb_type='both', page='3',
            list_slug='stale', sort_by='rank', sort_how='asc', cacheonly='False')
        self.assertEqual(result['info'], 'trakt_userlist')
        self.assertEqual(result['list_slug'], 'mindfuck')
        self.assertEqual(result['page'], '3')
        self.assertEqual(result['sort_by'], 'rank')
        self.assertEqual(result['sort_how'], 'asc')
        self.assertEqual(result['cacheonly'], 'False')

    def test_empty_random_list_pool_still_returns_empty(self):
        class EmptyLists(SampleLists):
            def get_items(self, **kwargs):
                return []
        wrapper = make_wrapper()
        wrapper.sample_class = EmptyLists
        self.assertEqual(wrapper.get_items(page=2), [])


if __name__ == '__main__':
    unittest.main()
