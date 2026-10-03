#!/usr/bin/env python3
"""Bump versions only after monthly extinguisher/report regressions pass."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
versions = {
    'android': ('3.29.136+278', '3.29.138+280'),
    'windows': ('3.30.56+243', '3.30.57+244'),
}
if platform not in versions:
    raise SystemExit('Use android or windows')
old, new = versions[platform]
path = root / 'pubspec.yaml'
source = path.read_text(encoding='utf-8')
if source.count('version: ' + old) != 1:
    raise SystemExit(f'Unexpected app version; expected {old}')
path.write_text(
    source.replace('version: ' + old, 'version: ' + new, 1),
    encoding='utf-8',
    newline='\n',
)
print('EXTINGUISHER_MONTHLY_VERSION_OK', new)
