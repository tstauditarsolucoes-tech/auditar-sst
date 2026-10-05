#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_management_training_cipa_ux_v329168_v33087.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo = Path(__file__).resolve().parents[1]
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

protected = [
    "lib/database.dart",
    "lib/models.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "lib/services/auditar_technical_inspection_pdf_service.dart",
    "lib/services/auditar_standard2_pdf_service.dart",
    "lib/services/auditar_standard3_pdf_service.dart",
    "lib/services/ronda_standard3_pdf_service.dart",
    "lib/services/express_round_pdf_service.dart",
    "lib/services/report_template_service.dart",
    "lib/services/styled_report_pdf_service.dart",
    "lib/services/report_logo_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {}
for name in protected:
    path = root / name
    if path.exists():
        before[name] = hashlib.sha256(path.read_bytes()).hexdigest()

copies = [
    ("feature_sources/manager_reports_module_v329168.dart", "lib/screens/manager_reports_screen.dart"),
    ("feature_sources/training_activity_center_v329168.dart", "lib/screens/training_activity_center_screen.dart"),
    ("feature_sources/cipa_management_screen_v329168.dart", "lib/screens/cipa_management_screen.dart"),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

pubp = root / "pubspec.yaml"
pub = pubp.read_text(encoding="utf-8")
if platform == "android":
    old_version = "3.29.167+309"
    new_version = "3.29.168+310"
else:
    old_version = "3.30.86+273"
    new_version = "3.30.87+274"
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
pubp.write_text(pub.replace(marker, "version: " + new_version, 1), encoding="utf-8", newline="\n")

after = {}
for name in before:
    after[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
changed = [name for name in before if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

(root / ".auditar_v329168_protected.json").write_text(
    json.dumps(after, indent=2, sort_keys=True),
    encoding="utf-8",
)

manager = (root / "lib/screens/manager_reports_screen.dart").read_text(encoding="utf-8")
training = (root / "lib/screens/training_activity_center_screen.dart").read_text(encoding="utf-8")
cipa = (root / "lib/screens/cipa_management_screen.dart").read_text(encoding="utf-8")
assert "Resumo para decisão" in manager
assert "CAPACITAÇÃO E CONTROLE PREVENTIVO" in manager
assert "Opções do relatório" in manager
assert "Planejamento anual" in training
assert "missingRequiredTrainings" in training
assert "Planejamento anual da CIPA" in cipa
assert "planejar" in cipa
assert "version: " + new_version in pubp.read_text(encoding="utf-8")

print("MANAGEMENT_TRAINING_CIPA_UX_OK", platform, new_version)
print("MANAGEMENT_DECISION_SUMMARY_OK")
print("TRAINING_PREVENTIVE_ANNUAL_VIEW_OK")
print("CIPA_ANNUAL_CALENDAR_OK")
print("ADVANCED_OPTIONS_COLLAPSED_OK")
print("PROTECTED_CORE_MANIFEST_OK")
