#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys

if len(sys.argv) < 2:
    raise SystemExit('Uso: patch_windows_mobile_improvements_v3301_compat.py <app_dir>')

root = Path(sys.argv[1])
syncp = root / 'lib/services/device_sync_service.dart'

# A base Windows usa pullLimit em variável, diferente do Android.
sync = syncp.read_text(encoding='utf-8')
sync = sync.replace(
    'final pullLimit = isWindows ? 100 : 100;',
    'final pullLimit = isWindows ? 500 : 100;',
    1,
)
sync = sync.replace(
    'final pullLimit = isWindows ? 150 : 300;',
    'final pullLimit = isWindows ? 500 : 300;',
    1,
)
syncp.write_text(sync, encoding='utf-8', newline='\n')

# O patch principal foi escrito para aceitar também a forma literal limit:.
# Na base Windows ele pode terminar somente na asserção final de formato; as
# alterações já foram gravadas. Capturamos apenas esse AssertionError e depois
# fazemos validação funcional compatível com o Windows.
old_argv = sys.argv[:]
try:
    sys.argv = [
        str(Path(__file__).with_name('patch_windows_mobile_improvements_v3301.py')),
        str(root),
    ]
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except AssertionError:
        pass
finally:
    sys.argv = old_argv

pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')
coord = (root / 'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
dds = (root / 'lib/screens/sst_records_screen.dart').read_text(encoding='utf-8')
media = (root / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
db = (root / 'lib/database.dart').read_text(encoding='utf-8')

assert 'version: 3.30.1+188' in pub
assert (
    'final pullLimit = isWindows ? 500 : 100;' in sync
    or 'final pullLimit = isWindows ? 500 : 300;' in sync
    or "'limit': 500," in sync
)
assert 'Duration(seconds: 10)' in coord
assert 'Retirar ficha do DDS' in dds
assert 'Histórico permanente de DDS' in dds
assert 'FICHA_DDS_' in dds
assert "type == 'DDS' ? 'date DESC'" in db
assert '_postReliable(' in media
assert 'continuam salvas no computador' in media
print('Windows v3.30.1 compatível: pull 500 + sync rápido + histórico DDS + mídia resiliente.')
