#!/usr/bin/env python3
"""Bump field UX release; on Windows align the Home version label."""
from pathlib import Path
import sys

if len(sys.argv) != 3 or sys.argv[2] not in ('android', 'windows'):
    raise SystemExit('usage: bump_polish_release_version_v1.py APP_DIR android|windows')
root = Path(sys.argv[1])
before, after = (
    ('3.29.197+339', '3.29.198+340')
    if sys.argv[2] == 'android'
    else ('3.30.125+312', '3.30.126+313')
)
pub = root / 'pubspec.yaml'
text = pub.read_text(encoding='utf-8')
old = 'version: ' + before
new = 'version: ' + after
assert text.count(old) == 1 and new not in text, 'Unexpected base version; release stopped'
updated = text.replace(old, new, 1)
assert updated.replace(new, old, 1) == text
if sys.argv[2] == 'windows':
    home = root / 'lib' / 'screens' / 'home_screen.dart'
    original_home = home.read_text(encoding='utf-8')
    previous_label = 'Auditar SST para Windows • versão 3.30.119'
    current_label = 'Auditar SST para Windows • versão 3.30.126'
    assert original_home.count(previous_label) == 1 and current_label not in original_home, (
        'Unexpected Windows Home version; release stopped'
    )
    updated_home = original_home.replace(previous_label, current_label, 1)
    assert updated_home.replace(current_label, previous_label, 1) == original_home
pub.write_text(updated, encoding='utf-8', newline='\n')
if sys.argv[2] == 'windows':
    home.write_text(updated_home, encoding='utf-8', newline='\n')
    assert home.read_text(encoding='utf-8').count(current_label) == 1
assert pub.read_text(encoding='utf-8').count(new) == 1
print('AUDITAR_FIELD_UX_VERSION_OK', sys.argv[2], after)
