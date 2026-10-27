#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${1:-app/Auditar_SST_v1_5_dashboard}"
python tools/assemble_sync_response_fix.py android
python tools/patch_sync_queue_android_v32940_v2.py "$APP_DIR"
python tools/patch_android_transport_guard_v32941.py "$APP_DIR"
python tools/patch_android_dns_bypass_v32942.py "$APP_DIR"
python tools/patch_android_dns_bypass_compile_fix.py "$APP_DIR"
python tools/patch_android_offline_background_sync_v32943.py "$APP_DIR"
python tools/patch_android_offline_compile_fix_v32943.py "$APP_DIR"
python tools/patch_android_sync_immediate_v32944.py "$APP_DIR"
python tools/patch_android_sync_first_pull_v32945.py "$APP_DIR"
python tools/patch_android_sync_core_v32946.py "$APP_DIR"
python tools/patch_dds_digital_signature_v32947.py "$APP_DIR"
python tools/patch_dds_formal_pdf_v32948.py "$APP_DIR"
python tools/patch_dds_formal_pdf_compile_fix_v32948.py "$APP_DIR"
python tools/patch_android_transport_ipv4_redirect_v32949.py "$APP_DIR"
python - <<'PY'
from pathlib import Path
root=Path('app/Auditar_SST_v1_5_dashboard')
pub=root/'pubspec.yaml'; coord=root/'lib/services/sync_coordinator.dart'
p=pub.read_text(encoding='utf-8'); c=coord.read_text(encoding='utf-8')
p=p.replace('version: 3.29.49+191','version: 3.29.50+192',1)
c=c.replace("const Duration(seconds: 10),\n      (_) => _trySync(deviceOnly: true, force: true),","const Duration(seconds: 2),\n      (_) => _trySync(deviceOnly: true, force: true),",1)
c=c.replace("const Duration(seconds: 30),\n      (_) {\n        _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n        _tryAutoBackup();\n      },","const Duration(seconds: 10),\n      (_) {\n        _trySync(deviceOnly: true, force: true, pullWhenClean: true);\n      },",1)
pub.write_text(p,encoding='utf-8'); coord.write_text(c,encoding='utf-8')
PY
python tools/patch_android_sync_latency_refresh_v32951.py "$APP_DIR"
python tools/patch_dds_sector_optional_v32952.py "$APP_DIR"
python tools/patch_dds_history_media_retry_v32953.py "$APP_DIR"
python tools/patch_company_logo_persistence_v32954_v3303.py "$APP_DIR" android
python - <<'PY'
from pathlib import Path
import re,base64,lzma
p=Path('app/Auditar_SST_v1_5_dashboard/lib/screens/companies_screen.dart')
s=p.read_text(encoding='utf-8')
s=re.sub(r'^\s*syncMedia:\s*false,\s*$', '', s, flags=re.M)
p.write_text(s,encoding='utf-8')
src=Path('build_sources/v3.29.55-ronda-ia-conformidade/patch_express_round_ai_conformity_v32955_v3304.py.xz.b64')
Path('/tmp/patch_ronda.py').write_bytes(lzma.decompress(base64.b64decode(src.read_text().strip())))
PY
python /tmp/patch_ronda.py "$APP_DIR" android
python - <<'PY'
from pathlib import Path
r=Path('app/Auditar_SST_v1_5_dashboard/lib/screens/express_round_screen.dart')
s=r.read_text(encoding='utf-8').replace('    final context = <String>[','    final technicianContext = <String>[',1).replace('      technicianContext: context,','      technicianContext: technicianContext,',1)
r.write_text(s,encoding='utf-8')
p=Path('app/Auditar_SST_v1_5_dashboard/lib/services/express_round_pdf_service.dart')
x=p.read_text(encoding='utf-8').replace('company.cnpj.trim().isNotEmpty', "(company.cnpj ?? '').trim().isNotEmpty").replace("_tableRow('CNPJ', company.cnpj)", "_tableRow('CNPJ', company.cnpj ?? '')")
p.write_text(x,encoding='utf-8')
PY
python tools/patch_ronda_ai_final_conclusion_v32956.py "$APP_DIR"
python tools/patch_sync_priority_v32957.py "$APP_DIR"
python tools/patch_sync_realtime_restore_v32958.py "$APP_DIR"
python tools/patch_ronda_ai_long_timeout_v32959.py "$APP_DIR"
python tools/patch_ronda_post_ai_photo_v32960.py "$APP_DIR"
python tools/patch_ronda_deferred_ai_timeout_v32960.py "$APP_DIR"
echo "Fonte Android v3.29.60 montada."