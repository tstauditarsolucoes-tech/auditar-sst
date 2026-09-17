#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys

repo=Path(__file__).resolve().parents[1]
root=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'app/Auditar_SST_v1_5_dashboard'
if not root.is_absolute():
    root=(repo/root).resolve()
py=sys.executable


def run(script,*args):
    subprocess.check_call([py,str(repo/script),*map(str,args)],cwd=repo)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

# Base Windows atual com todos os recursos de relatório.
run('tools/assemble_windows_v3305_report_templates.py',root)
protected=[
    root/'lib/services/device_sync_service.dart',
    root/'lib/services/media_sync_service.dart',
    root/'lib/services/apps_script_http.dart',
    root/'lib/services/sync_coordinator.dart',
    root/'lib/services/drive_service.dart',
]
before={p:digest(p) for p in protected}

run('tools/patch_neutral_sst_edition_v1_fixed.py',root)
run('tools/patch_neutral_env_v1.py',root)
run('tools/regression_neutral_sst_v1.py',root)

after={p:digest(p) for p in protected}
changed=[str(p.relative_to(root)) for p in protected if before[p]!=after[p]]
if changed:
    raise RuntimeError('Proteção do núcleo falhou: '+', '.join(changed))

# Comportamento específico de desktop continua o mesmo.
coord=(root/'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
dev=(root/'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
assert 'Duration(seconds: 10)' in coord
assert 'final pullLimit = isWindows ? 500 : 100;' in dev

print('NEUTRAL_WINDOWS_V1_OK: núcleo Windows preservado; banco/login/backup da edição neutra ficam isolados.')
for p in protected:
    print('NUCLEO_SYNC_INTACTO',p.relative_to(root),after[p])
