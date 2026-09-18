#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-app/Auditar_SST_v1_5_dashboard}"

# Usa a base rapida e conhecida, sem herdar a v3.29.63/64.
bash tools/assemble_android_v32962.sh "$ROOT"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib, json, sys
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
]
state={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.exists()}
Path('/tmp/auditar_v32965_sync_protected.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
PY

python3 tools/patch_rh_pdf_import_isolated_v32964.py "$ROOT"
python3 tools/patch_rh_pdf_local_text_v32965.py "$ROOT"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1])
before=json.loads(Path('/tmp/auditar_v32965_sync_protected.json').read_text(encoding='utf-8'))
changed=[]
for rel, old in before.items():
    p=root/rel
    new=hashlib.sha256(p.read_bytes()).hexdigest()
    if new != old:
        changed.append(rel)
    else:
        print('SYNC_PROTEGIDO_OK', rel, new)
if changed:
    raise SystemExit('PROTECAO DE SYNC: v3.29.65 alterou arquivos protegidos: '+', '.join(changed))

svc=(root/'lib/services/worker_import_service.dart').read_text(encoding='utf-8')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: 3.29.65+207' in pub
assert 'read_pdf_text: ^0.3.1' in pub
assert 'ReadPdfText.getPDFtext' in svc
assert '_buildLightweightRhPdf' in svc
assert '_postPdfImportDedicated' in svc
assert 'AppsScriptHttp.postJson' not in svc
print('ANDROID_V32965_OK: leitura local RH + cliente dedicado; sync v3.29.62 preservado byte por byte.')
PY
