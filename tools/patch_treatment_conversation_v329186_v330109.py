#!/usr/bin/env python3
"""Show treatment drafts per conversation without changing protected SST services or GS."""
from pathlib import Path
import hashlib
import shutil
import sys

root = Path(sys.argv[1])
platform = sys.argv[2]
assert platform in ('android', 'windows')
repo = Path(__file__).resolve().parents[1]
target = root / 'lib/screens/client_treatment_inbox_screen.dart'
test = root / 'test/treatment_outbox_test.dart'
assert target.is_file() and test.is_file(), 'Base tratativas 185/108 ausente'
old_version, new_version = (
    ('3.29.185+327', '3.29.186+328') if platform == 'android'
    else ('3.30.108+295', '3.30.109+296')
)
pubspec = root / 'pubspec.yaml'
orig = pubspec.read_text(encoding='utf-8')
assert orig.count('version: ' + old_version) == 1, 'Versão base inesperada'
protected = [
    path for folder in ('lib', 'painel_web_google_apps_script')
    for path in (root / folder).rglob('*')
    if path.is_file() and path != target
]
hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
shutil.copyfile(repo / 'feature_sources/client_treatment_inbox_screen_v329186.dart', target)
shutil.copyfile(repo / 'feature_sources/treatment_outbox_test_v329186.dart', test)
pubspec.write_text(orig.replace('version: ' + old_version,
                                'version: ' + new_version), encoding='utf-8')
for path, checksum in hashes.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum, str(path)
print('TRATATIVAS_CONVERSA_LOCAL_OK; app '+new_version+'; SST core, GS, media unchanged')
