"""A successful Trakt sync action (mark watched, add to list...) shows a toast; a failure keeps the OK box."""
import importlib.util
from functools import cached_property
from pathlib import Path
from types import ModuleType
import sys
import unittest
from unittest.mock import MagicMock, patch


SOURCE = Path(__file__).resolve().parents[1] / 'resources/tmdbhelper/lib/script/sync/item.py'
STRINGS = {32296: '{} failed for {}!\n{} ID {}', 32297: '{} was successful for {}!\n{} ID {}'}


def load_item(dialog):
    modules = {}
    for name, values in {
        'jurialmunkey.ftools': {'cached_property': cached_property},
        'tmdbhelper.lib.addon.plugin': {'get_localized': lambda i: STRINGS.get(i, str(i))},
        'xbmcgui': {'Dialog': lambda: dialog},
    }.items():
        module = ModuleType(name)
        module.__dict__.update(values)
        modules[name] = module
    spec = importlib.util.spec_from_file_location('sync_item_under_test', SOURCE)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


def make_item(module, status_code):
    cls = next(v for v in vars(module).values() if isinstance(v, type) and hasattr(v, 'display_dialog'))
    item = cls.__new__(cls)
    item.__dict__.update({
        'sync_response': {'ok': True}, 'status_code': status_code, 'confirm_success': True,
        'name': 'Mark as watched', 'item_name': 'Dune', 'tmdb_type': 'movie', 'item_id': 438631,
    })
    return item


class SyncDialogTest(unittest.TestCase):
    def test_success_is_a_toast(self):
        dialog = MagicMock()
        make_item(load_item(dialog), 201).display_dialog()
        dialog.notification.assert_called_once_with('Mark as watched', 'Mark as watched was successful for Dune!')
        dialog.ok.assert_not_called()

    def test_failure_keeps_ok_box(self):
        dialog = MagicMock()
        make_item(load_item(dialog), 500).display_dialog()
        dialog.ok.assert_called_once()
        dialog.notification.assert_not_called()


if __name__ == '__main__':
    unittest.main()
