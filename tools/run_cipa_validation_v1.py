#!/usr/bin/env python3
"""Focused diagnostic artifact; exit nonzero on the first real failure."""
from pathlib import Path
import shutil
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
app = Path(sys.argv[1]).resolve()
platform = sys.argv[2]
if platform not in ('android', 'windows'):
    raise SystemExit('Invalid platform')
output = repo / 'dist' / ('CIPA-Diagnostico-' + platform)
output.mkdir(parents=True, exist_ok=True)
dart = shutil.which('dart')
flutter = shutil.which('flutter')
if not dart or not flutter:
    raise SystemExit('Dart/Flutter missing')
source = app / 'lib/screens/cipa_management_screen.dart'
if source.exists():
    shutil.copyfile(source, output / 'cipa_before.dart')
commands = [
    (repo, [sys.executable, 'tools/test_cipa_participation_v1.py']),
    (repo, [sys.executable, 'tools/patch_cipa_participation_v1.py', str(app), platform]),
    (repo, [sys.executable, 'tools/bump_cipa_release_v1.py', str(app), platform]),
    (app, [dart, 'format', 'lib/screens/cipa_management_screen.dart',
           'lib/screens/cipa_participation_screen.dart', 'lib/services/cipa_participation_rules.dart',
           'test/cipa_participation_rules_test.dart']),
    (app, [flutter, 'analyze', '--no-fatal-infos', '--no-fatal-warnings']),
    (app, [dart, 'test/cipa_participation_rules_test.dart']),
]
with (output / 'validation.log').open('w', encoding='utf-8') as log:
    for cwd, args in commands:
        print('RUN', args, flush=True)
        log.write('RUN ' + repr(args) + '\n')
        log.flush()
        done = subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
        if done.returncode:
            if source.exists():
                shutil.copyfile(source, output / 'cipa_after.dart')
            log.flush()
            print((output / 'validation.log').read_text(encoding='utf-8')[-14000:])
            raise SystemExit(done.returncode)
print('CIPA: fixtures, protected patch, format, full analysis and rules passed')
