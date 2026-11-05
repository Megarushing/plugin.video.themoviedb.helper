"""Contracts our mega changes depend on after merging upstream 6.20.x (provider split)."""
import ast
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
STRINGS = ROOT / 'resources/language/resource.language.en_gb/strings.po'
SETTINGS = ROOT / 'resources/settings.xml'
CONSTS = ROOT / 'resources/tmdbhelper/lib/addon/consts.py'
LISTS_STANDARD = ROOT / 'resources/tmdbhelper/lib/items/directories/sync/lists_standard.py'
LISTS_RANDOM = ROOT / 'resources/tmdbhelper/lib/items/directories/sync/lists_random.py'


def strings():
    return re.findall(r'msgctxt "#(\d+)"\nmsgid "(.*)"', STRINGS.read_text())


class StringIds(unittest.TestCase):
    def test_no_duplicate_string_ids(self):
        ids = [i for i, _ in strings()]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        self.assertEqual(dupes, [])

    def test_every_settings_label_exists(self):
        known = {i for i, _ in strings()}
        root = ElementTree.parse(SETTINGS).getroot()
        used = set()
        for el in root.iter():
            for attr in ('label', 'help'):
                v = el.get(attr, '')
                if v.isdigit() and 32000 <= int(v) < 33000:
                    used.add(v)
            if el.tag == 'heading' and (el.text or '').isdigit() and 32000 <= int(el.text) < 33000:
                used.add(el.text)
        self.assertEqual(sorted(used - known), [])

    def test_provider_region_setting_uses_its_own_strings(self):
        texts = dict(strings())
        setting = next(s for s in ElementTree.parse(SETTINGS).getroot().iter('setting') if s.get('id') == 'provider_region')
        self.assertEqual(texts[setting.get('label')], 'Provider region')
        self.assertTrue(texts[setting.get('help')].startswith('Two-letter country code'))
        self.assertEqual(setting.find('control/heading').text, setting.get('label'))


class Routes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(CONSTS.read_text())
        cls.src = CONSTS.read_text()
        cls.noid = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                        and getattr(n.targets[0], 'id', '') == 'ROUTE_NOID')

    def test_sync_activity_route(self):
        route = ast.literal_eval(self.noid)['sync_activity']['route']
        self.assertEqual(route['module_name'], 'tmdbhelper.lib.items.directories.sync.lists_standard')
        self.assertEqual(route['import_attr'], 'ListActivity')
        classes = {n.name for n in ast.parse(LISTS_STANDARD.read_text()).body if isinstance(n, ast.ClassDef)}
        self.assertIn('ListActivity', classes)

    def test_trakt_activity_alias_for_the_skin(self):
        self.assertIn("'trakt_activity': ROUTE_NOID['sync_activity']", self.src)


class BecauseYouWatchedStablePick(unittest.TestCase):
    def test_uses_stable_daily_pick(self):
        src = LISTS_RANDOM.read_text()
        self.assertIn('stable_random(self.paramstring).choice(watched_items)', src)
        self.assertNotIn('random.randint', src)


if __name__ == '__main__':
    unittest.main()
