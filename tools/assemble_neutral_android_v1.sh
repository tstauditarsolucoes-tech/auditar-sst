#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-app/Auditar_SST_v1_5_dashboard}"

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
 root/'lib/services/drive_service.dart',
]
state={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
Path('/tmp/sst_neutral_android_protected.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
PY

python3 tools/patch_neutral_sst_edition_v1_fixed2.py "$ROOT"
python3 tools/patch_neutral_brand_widget_compat_v1.py "$ROOT"
python3 tools/patch_neutral_env_v1.py "$ROOT"
python3 tools/patch_neutral_final_identity_v1.py "$ROOT"
python3 tools/patch_neutral_epi_module_v1.py "$ROOT"
python3 tools/patch_neutral_tests_v1.py "$ROOT"
python3 tools/regression_neutral_sst_v1.py "$ROOT"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1])
before=json.loads(Path('/tmp/sst_neutral_android_protected.json').read_text(encoding='utf-8'))
changed=[]
for rel, old in before.items():
    p=root/rel
    new=hashlib.sha256(p.read_bytes()).hexdigest()
    if new != old:
        changed.append(rel)
    else:
        print('NUCLEO_SYNC_INTACTO',rel,new)
if changed:
    raise SystemExit('Proteção do núcleo falhou: '+', '.join(changed))
print('NEUTRAL_ANDROID_V1_OK: núcleo de sincronização byte por byte preservado.')
PY
