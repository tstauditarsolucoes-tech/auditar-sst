#!/usr/bin/env python3
"""Safely bump version for field UX release. Only pubspec.yaml is written."""
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
pub.write_text(updated, encoding='utf-8', newline='\n')
assert pub.read_text(encoding='utf-8').count(new) == 1
print('AUDITAR_FIELD_UX_VERSION_OK', sys.argv[2], after)
