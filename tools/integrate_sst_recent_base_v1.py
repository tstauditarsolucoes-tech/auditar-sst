#!/usr/bin/env python3
"""Integrar SOMENTE o Centro SST nas fontes recentes dos candidatos da CI.

Não altera base de dados, sync, auth, fotos, IA, Apps Script ou PDF vigente.
Usar em cópia integral gerada pela CI, NUNCA em computador do cliente.
Não reaplicar os patches legados de CIPA/NR12 nem o bloqueio de assinatura
antiga: a fonte recente já inclui revisões desses módulos, e sobrescrevê-las
pode causar regressões e duplicação.
"""
from pathlib import Path
import hashlib
import subprocess
import sys

if len(sys.argv) != 3 or sys.argv[2] not in ("android", "windows"):
    raise SystemExit("Uso: integrate_sst_recent_base_v1.py <APP_DIR> android|windows")

root = Path(sys.argv[1]).resolve()
platform = sys.argv[2]
repo = Path(__file__).resolve().parents[1]
pub = root / "pubspec.yaml"

if not root.is_dir() or not pub.is_file():
    raise SystemExit("BLOQUEADO: projeto Flutter integral ausente.")
expected = ("3.29.200+342" if platform == "android" else "3.30.128+315")
source = pub.read_text(encoding="utf-8")
if source.count("version: " + expected) != 1:
    raise SystemExit("BLOQUEADO: origem divergente, esperado " + expected)
if not (root / "lib" / "database.dart").is_file():
    raise SystemExit("BLOQUEADO: app integral não contém o banco existente.")

required = [
    "lib/models.dart",
    "lib/services/auth_service.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/screens/company_detail_screen.dart",
    "lib/screens/quick_visit_screen.dart",
    "lib/screens/express_round_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/screens/manager_reports_screen.dart",
    "painel_web_google_apps_script/Code.gs",
]
absent = [path for path in required if not (root / path).is_file()]
if absent:
    raise SystemExit("BLOQUEADO: base incompleta: " + ", ".join(absent))

protected = [
    "lib/database.dart", "lib/models.dart",
    "lib/services/auth_service.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/screens/express_round_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/screens/report_screen.dart",
    "lib/screens/signature_screen.dart",
    "lib/screens/checklist_screen.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
]
# Android tinha o patch de conclusão que já preserva o registro e o envio.
if platform == "android":
    protected.remove("lib/screens/express_round_screen.dart")
before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
          for name in protected if (root / name).is_file()}

steps = (
    ["tools/patch_android_unified_visits_v1.py",
     "tools/patch_android_standard_conclusion_v1.py"]
    if platform == "android"
    else ["tools/patch_windows_smart_visit_v1.py"]
)
# Só os relatórios/guias novos; funcionalidades atuais de CIPA, NR-12 e
# assinatura antiga ficam BYTE A BYTE idênticas.
steps += ["tools/patch_sst_report_center_v1.py"]
for name in steps:
    print("INTEGRACAO_RECENTE_EXECUTAR", name, flush=True)
    proc = subprocess.run([sys.executable, str(repo / name), str(root)],
                          cwd=str(repo), check=False)
    if proc.returncode:
        raise SystemExit(
            "INTEGRAÇÃO BLOQUEADA em " + name +
            "; manter versão instalada e NÃO distribuir."
        )
    changed = [
        path for path, old in before.items()
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != old
    ]
    if changed:
        raise SystemExit("NUCLEO_PROTEGIDO_ALTERADO: " + ", ".join(changed))

needed = [
    "lib/screens/sst_report_center_screen.dart",
    "lib/screens/sst_risk_documents_screen.dart",
    "lib/screens/sst_pet_nr33_screen.dart",
    "lib/screens/sst_activity_guide_screen.dart",
    "lib/screens/sst_document_signature_panel.dart",
    "lib/services/sst_risk_documents_models.dart",
    "lib/services/sst_pet_nr33_models.dart",
    "lib/services/sst_activity_guide_models.dart",
    "lib/services/sst_document_signature_models.dart",
    "lib/services/sst_scope_key.dart",
    "test/sst_risk_documents_test.dart",
    "test/sst_pet_nr33_test.dart",
    "test/sst_activity_guide_test.dart",
    "test/sst_document_signature_test.dart",
]
missing = [name for name in needed if not (root / name).is_file()]
if missing:
    raise SystemExit("INTEGRACAO_INCOMPLETA: " + ", ".join(missing))
if platform == "android":
    source = pub.read_text(encoding="utf-8")
    if source.count("version: " + expected) != 1:
        raise SystemExit("Versão alterada inesperadamente durante os patches.")
    pub.write_text(
        source.replace("version: " + expected, "version: 3.29.202+344", 1),
        encoding="utf-8",
    )
print("SST_FONTE_RECENTE_INTEGRADA", platform, "PASSOU_NUCLEO_PROTEGIDO",
      flush=True)
