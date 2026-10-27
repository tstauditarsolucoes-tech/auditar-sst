#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-app/Auditar_SST_v1_5_dashboard}"

bash tools/assemble_android_v32962.sh "$ROOT"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1])
protected=[
 root/'lib/services/device_sync_service.dart',
 root/'lib/services/media_sync_service.dart',
 root/'lib/services/apps_script_http.dart',
 root/'lib/services/sync_coordinator.dart',
 root/'lib/services/auth_service.dart',
 root/'lib/services/drive_service.dart',
 root/'lib/database.dart',
 root/'lib/services/web_service_config.dart',
 root/'painel_web_google_apps_script/Code.gs',
]
data={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.exists()}
Path('/tmp/auditar_v32966_protected.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
PY

python3 tools/patch_rh_pdf_import_isolated_v32964.py "$ROOT"
python3 tools/patch_rh_pdf_local_text_v32965.py "$ROOT"
python3 tools/patch_rh_pdf_local_parser_v32966.py "$ROOT"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib,json,sys
root=Path(sys.argv[1])
before=json.loads(Path('/tmp/auditar_v32966_protected.json').read_text(encoding='utf-8'))
changed=[]
for rel,old in before.items():
    p=root/rel; new=hashlib.sha256(p.read_bytes()).hexdigest()
    if new!=old: changed.append(rel)
    else: print('PROTEGIDO_OK',rel,new)
if changed:
    raise SystemExit('v3.29.66 alterou arquivos protegidos: '+', '.join(changed))
svc=(root/'lib/services/worker_import_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 3.29.66+208' in pub
assert 'parseExtractedRhTextForTesting' in svc
assert 'Total\\s+Geral' in svc
assert "const ['Nome', 'Cargo', 'Setor']" in svc
print('ANDROID_V32966_OK: parser RH local; sync, Central, GS e banco preservados.')
PY
