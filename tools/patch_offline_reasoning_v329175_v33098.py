#!/usr/bin/env python3
"""Add deterministic suggestion review without changing existing services/storage."""
from pathlib import Path
import hashlib
import shutil
import sys
root = Path(sys.argv[1])
platform = sys.argv[2]
assert platform in ('android', 'windows')
repo = Path(__file__).resolve().parents[1]
widget = root / 'lib/widgets/offline_report_inline_suggestions.dart'
service = root / 'lib/services/offline_reasoning.dart'
assert widget.exists() and not service.exists(), 'Unexpected offline baseline'
protected = [p for folder in ('lib', 'painel_web_google_apps_script')
             for p in (root / folder).rglob('*') if p.is_file() and p != widget]
before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
for source, target in [
    ('offline_reasoning_v329175.dart', service),
    ('offline_report_inline_suggestions_v329175.dart', widget),
    ('offline_reasoning_test_v329175.dart', root / 'test/offline_reasoning_test.dart'),
]:
    shutil.copyfile(repo / 'feature_sources' / source, target)
p = root / 'pubspec.yaml'
s = p.read_text(encoding='utf-8')
old, new = ('3.29.174+316', '3.29.175+317') if platform == 'android' else ('3.30.97+284', '3.30.98+285')
assert s.count('version: ' + old) == 1
p.write_text(s.replace('version: ' + old, 'version: ' + new), encoding='utf-8', newline='\n')
for path, digest in before.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
print('OFFLINE_REASONING_READY; ALL_EXISTING_SERVICES_DATABASE_MODELS_SCREENS_CENTRAL_BYTE_IDENTICAL', platform)
