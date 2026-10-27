#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-app/Auditar_SST_v1_5_dashboard}"

bash tools/assemble_android_v32961.sh "$ROOT"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1])
fixed=[
 root/'lib/services/device_sync_service.dart',
 root/'lib/services/media_sync_service.dart',
 root/'lib/services/auth_service.dart',
 root/'lib/services/drive_service.dart',
 root/'lib/database.dart',
 root/'lib/services/web_service_config.dart',
]
extra=sorted((root/'lib/services').glob('*transport*.dart'))+sorted((root/'lib/services').glob('*apps_script*.dart'))
paths=[]
for p in fixed+extra:
    if p.exists() and p not in paths: paths.append(p)
data={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
Path('/tmp/auditar_report_templates_android_protected.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
PY

python3 tools/patch_report_templates_v32962.py "$ROOT"
python3 tools/patch_report_templates_user_default_v32962.py "$ROOT"
python3 tools/patch_report_templates_compile_fix_v32962.py "$ROOT"

python3 - "$ROOT" <<'PY'
from pathlib import Path
import hashlib, json, sys
root=Path(sys.argv[1])
before=json.loads(Path('/tmp/auditar_report_templates_android_protected.json').read_text(encoding='utf-8'))
changed=[]
for rel, old in before.items():
    p=root/rel
    new=hashlib.sha256(p.read_bytes()).hexdigest()
    if new != old: changed.append(rel)
    else: print('SYNC_PROTEGIDO_OK', rel, new)
if changed:
    raise SystemExit('PROTEÇÃO DE SYNC: atualização de relatórios alterou: '+', '.join(changed))

pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
templates=(root/'lib/services/report_template_service.dart').read_text(encoding='utf-8')
pdf=(root/'lib/services/pdf_service.dart').read_text(encoding='utf-8')
assert 'version: 3.29.62+204' in pub
assert "name: 'Padrão Auditar atual'" in templates
assert 'useLegacyRenderer: true' in templates
assert 'selectDefaultForCurrentUser' in templates
assert 'AuthService.currentUser?.id' in templates
assert 'if (!reportTemplate.useLegacyRenderer)' in pdf
print('ANDROID_V32962_OK: modelos + padrão individual por usuário adicionados; sincronização/login/mídia/Drive/banco preservados byte por byte.')
PY

echo "Fonte Android v3.29.62 montada."
