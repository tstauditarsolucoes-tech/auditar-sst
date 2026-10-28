#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3 or sys.argv[2] not in ('android', 'windows'):
    raise SystemExit('usage: bump_cipa_release_v1.py APP_DIR android|windows')
root = Path(sys.argv[1])
old, new = ('3.29.198+340', '3.29.199+341') if sys.argv[2] == 'android' else ('3.30.126+313', '3.30.127+314')
pub = root / 'pubspec.yaml'
text = pub.read_text(encoding='utf-8')
if text.count('version: ' + old) != 1: raise SystemExit('Unexpected version; release stopped')
if sys.argv[2] == 'windows':
    home = root / 'lib/screens/home_screen.dart'
    before = home.read_text(encoding='utf-8')
    marker = 'Auditar SST para Windows • versão 3.30.126'
    if before.count(marker) != 1: raise SystemExit('Unexpected Home version; release stopped')
    home.write_text(before.replace(marker, 'Auditar SST para Windows • versão 3.30.127'), encoding='utf-8')
pub.write_text(text.replace('version: ' + old, 'version: ' + new), encoding='utf-8')
print('CIPA_RELEASE_VERSION_OK', new)
