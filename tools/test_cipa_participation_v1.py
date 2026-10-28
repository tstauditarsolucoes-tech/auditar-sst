#!/usr/bin/env python3
"""Test both generated layouts, fail-closed patching and protected-file hashes."""
from pathlib import Path
import importlib.util
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('cipa_patch', ROOT / 'tools/patch_cipa_participation_v1.py')
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


class CipaPatchTest(unittest.TestCase):
    def fixture(self, platform):
        source = (ROOT / 'feature_sources/cipa_management_screen_v329168.dart').read_text(encoding='utf-8')
        if platform == 'windows':
            desktop = (ROOT / 'tools/patch_windows_desktop_ux_v330118.py').read_text(encoding='utf-8')
            start = desktop.index('# 2. CIPA:')
            end = desktop.index('# 3. Timeline:')
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / 'cipa.dart'
                exec(desktop[start:end], {'pre': {'cipa': source}, 'paths': {'cipa': path},
                    'one': lambda text, old, new, name: patch.replace_once(text, old, new), 're': re})
                source = path.read_text(encoding='utf-8')
        if shutil.which('dart'):
            with tempfile.TemporaryDirectory() as td:
                p = Path(td) / 'screen.dart'
                p.write_text(source, encoding='utf-8')
                subprocess.run(['dart', 'format', str(p)], check=True, capture_output=True)
                source = p.read_text(encoding='utf-8')
        return source

    def test_both_platforms_and_integrity(self):
        for platform in ('android', 'windows'):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as td:
                app = Path(td)
                screen = app / 'lib/screens/cipa_management_screen.dart'
                screen.parent.mkdir(parents=True)
                screen.write_text(self.fixture(platform), encoding='utf-8')
                for name in ['lib/database.dart', 'lib/models.dart', 'lib/services/auth_service.dart',
                             'lib/services/cipa_management_service.dart', 'lib/services/media_sync_service.dart',
                             'painel_web_google_apps_script/Code.gs']:
                    p = app / name
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text('UNCHANGED SENTINEL ' + name, encoding='utf-8')
                before = patch.snapshot(app)
                patch.main(app, platform)
                self.assertEqual(before, patch.snapshot(app))
                output = screen.read_text(encoding='utf-8')
                self.assertIn('length: 11', output)
                self.assertEqual(output.count('_cipaWorkspaceTab(),'), 2)
                self.assertIn("'Participação'", output)
                self.assertIn("current.payload['mandateId']", output)
                self.assertNotIn('deleteSstRecord', output)
                self.assertNotIn('deleteRecord(', output)
                self.assertIn('const Uuid().v4()', output)
                if platform == 'windows':
                    self.assertIn('Icons.volunteer_activism_outlined', output)
                    self.assertIn('final controller = DefaultTabController.of(tabsContext);', output)
                if shutil.which('dart'):
                    subprocess.run(['dart', 'format', str(screen),
                        str(app / 'lib/screens/cipa_participation_screen.dart')], check=True)
                    subprocess.run(['dart', str(app / 'test/cipa_participation_rules_test.dart')], check=True)
                with self.assertRaises(RuntimeError):
                    patch.main(app, platform)

    def test_missing_anchor_fails(self):
        with self.assertRaises(RuntimeError): patch.transform('unrelated screen', 'android')


if __name__ == '__main__': unittest.main()
