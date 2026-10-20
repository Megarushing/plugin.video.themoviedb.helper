"""Regression tests for the real resolver; only Kodi dependencies are stubbed."""
import importlib.util
from functools import cached_property
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'resources/tmdbhelper/lib/player/action/resolver.py'


def load_resolver():
    modules = {}
    for name, values in {
        'jurialmunkey.ftools': {'cached_property': cached_property},
        'tmdbhelper.lib.addon.plugin': {
            'executebuiltin': lambda *args: None,
            'format_folderpath': lambda value: value,
        },
        'tmdbhelper.lib.addon.logger': {'kodi_log': lambda *args: None},
    }.items():
        module = ModuleType(name)
        module.__dict__.update(values)
        modules[name] = module
    spec = importlib.util.spec_from_file_location('resolver_under_test', SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class Details:
    def __init__(self):
        self.params = {'info': 'play'}
        self.path = 'plugin://listing/original'
        self.infoproperties = {'ResumeTime': 4257, 'TotalTime': 5647, 'Other': 'preserve'}

    @cached_property
    def url(self):
        return self.path

    def get_listitem(self):
        # Snapshot what the real resolver hands to Kodi's ListItem constructor.
        return SimpleNamespace(path=self.url, properties=dict(self.infoproperties))


class ResolverResumeTests(unittest.TestCase):
    def setUp(self):
        self.module = load_resolver()
        self.details = Details()
        player = SimpleNamespace(item=SimpleNamespace(details=self.details))
        self.resolver = self.module.PlayerResolverNone(player, handle=7)
        self.resolver.path = 'plugin://plugin.video.elementum/library/play/movie/1213997'
        self.resolver.is_folder = False

    def invoke(self, flag):
        argv = ['plugin://plugin.video.themoviedb.helper/', '7', '?info=play']
        if flag is not None:
            argv.append(flag)
        with patch.object(sys, 'argv', argv):
            return self.resolver.listitem

    def test_cached_listing_url_is_not_used_as_playback_path(self):
        self.assertEqual(self.details.url, 'plugin://listing/original')
        self.assertEqual(self.invoke('resume:false').path, self.resolver.path)
        self.assertEqual(self.details.url, 'plugin://listing/original')

    def test_resume_keeps_resume_metadata(self):
        item = self.invoke('resume:true')
        self.assertEqual(item.properties['ResumeTime'], 4257)
        self.assertEqual(item.properties['TotalTime'], 5647)

    def test_legacy_invocation_keeps_existing_behavior(self):
        self.assertEqual(self.invoke(None).properties['ResumeTime'], 4257)

    def test_case_insensitive_no_resume_is_honoured(self):
        self.assertNotIn('ResumeTime', self.invoke('RESUME:FALSE').properties)

    def test_missing_resume_metadata_does_not_error(self):
        self.details.infoproperties = {'Other': 'preserve'}
        self.assertEqual(self.invoke('resume:false').properties['Other'], 'preserve')

    def test_folder_flags_are_preserved(self):
        self.resolver.is_folder = True
        item = self.invoke('resume:false')
        self.assertEqual(item.properties['isPlayable'], 'false')
        self.assertEqual(item.properties['is_folder'], 'true')

    def test_listing_metadata_is_not_changed_by_beginning(self):
        before = dict(self.details.infoproperties)
        self.invoke('resume:false')
        self.assertEqual(self.details.infoproperties, before)
        self.assertEqual(self.details.path, 'plugin://listing/original')
        self.assertEqual(self.details.params, {'info': 'play'})

    def test_explicit_beginning_does_not_return_resume_metadata(self):
        item = self.invoke('resume:false')
        self.assertNotIn('ResumeTime', item.properties)
        self.assertNotIn('TotalTime', item.properties)
        self.assertEqual(item.properties['Other'], 'preserve')
        self.assertEqual(item.path, self.resolver.path)


if __name__ == '__main__':
    unittest.main()
