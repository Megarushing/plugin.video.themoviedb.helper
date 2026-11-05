"""Every decorator name a module uses must be defined or imported in that module.

A merge can keep our code that uses a decorator while upstream drops the import (episode.py lost
`cached_property` in the 6.20.8 merge: every episode list raised NameError and came back empty).
Compiling does not catch this; it only fails when the module is imported on the device."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'resources'
BUILTIN = {'property', 'staticmethod', 'classmethod'}


def bound_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update((a.asname or a.name).split('.')[0] for a in node.names)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


class DecoratorImports(unittest.TestCase):
    def test_decorators_are_bound(self):
        missing = []
        for path in sorted(ROOT.rglob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            bound = bound_names(tree) | BUILTIN
            for node in ast.walk(tree):
                for dec in getattr(node, 'decorator_list', ()):
                    base = dec.func if isinstance(dec, ast.Call) else dec
                    while isinstance(base, ast.Attribute):
                        base = base.value
                    if isinstance(base, ast.Name) and base.id not in bound:
                        missing.append(f'{path.relative_to(ROOT)}:{dec.lineno} {base.id}')
        self.assertEqual(missing, [])


if __name__ == '__main__':
    unittest.main()
