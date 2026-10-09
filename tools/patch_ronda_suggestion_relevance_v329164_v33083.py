#!/usr/bin/env python3
"""Auditar SST v3.29.164 / v3.30.83 — refinamento da captura da Ronda.

- melhora a relevância das sugestões locais;
- prioriza botão/parada de emergência corretamente;
- evita sugestões genéricas sem relação;
- compacta o bloco visual de sugestões;
- deixa a ação de matriz/NR menos dominante.

Sem alterações em banco, sync, auth, HTTP, mídia/Drive, IA ou Apps Script.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_ronda_suggestion_relevance_v329164_v33083.py "
        "<APP_DIR> <android|windows>"
    )

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
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
    if (root / name).exists()
}

copies = [
    (
        "feature_sources/offline_report_inline_suggestions_v329164.dart",
        "lib/widgets/offline_report_inline_suggestions.dart",
    ),
    (
        "feature_sources/offline_report_inline_suggestions_test_v329164.dart",
        "test/offline_report_inline_suggestions_test.dart",
    ),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

# Ronda: mesma função, hierarquia visual mais discreta e nome mais claro.
ronda_path = root / "lib/screens/express_round_screen.dart"
ronda = ronda_path.read_text(encoding="utf-8")

old_label = "label: const Text('Matriz e NR sem IA'),"
new_label = "label: const Text('Analisar risco e NR sem IA'),"
if new_label not in ronda:
    if old_label not in ronda:
        raise RuntimeError("botao Matriz e NR sem IA nao localizado")
    pos = ronda.index(old_label)
    start = ronda.rfind("FilledButton.tonalIcon(", 0, pos)
    if start < 0:
        raise RuntimeError("tipo do botao Matriz e NR sem IA nao localizado")
    ronda = ronda[:start] + ronda[start:].replace(
        "FilledButton.tonalIcon(",
        "OutlinedButton.icon(",
        1,
    )
    ronda = ronda.replace(old_label, new_label, 1)

ronda_path.write_text(ronda, encoding="utf-8", newline="\n")

# Versão.
pub_path = root / "pubspec.yaml"
pub = pub_path.read_text(encoding="utf-8")
old_version, new_version = (
    ("3.29.163+305", "3.29.164+306")
    if platform == "android"
    else ("3.30.82+269", "3.30.83+270")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
pub_path.write_text(
    pub.replace(marker, "version: " + new_version, 1),
    encoding="utf-8",
    newline="\n",
)

after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
    if (root / name).exists()
}
changed = [name for name in before if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

widget = (root / "lib/widgets/offline_report_inline_suggestions.dart").read_text(
    encoding="utf-8"
)
ronda = ronda_path.read_text(encoding="utf-8")

for snippet in (
    "auditar-botao-emergencia-inoperante",
    "Sugestões mais próximas",
    "sem internet",
    "Ver mais ",
    "_noiseTokens",
    "_concepts(",
):
    assert snippet in widget, "refinamento ausente: " + snippet

assert "Analisar risco e NR sem IA" in ronda
assert "Matriz e NR sem IA" not in ronda
assert "version: " + new_version in pub_path.read_text(encoding="utf-8")

print("RONDA_SUGGESTION_RELEVANCE_OK", platform, new_version)
print("EMERGENCY_STOP_RANKING_OK")
print("COMPACT_SUGGESTION_UI_OK")
print("CORE_SYNC_DB_AUTH_HTTP_MEDIA_DRIVE_AI_GS_REPORTS_UNCHANGED_OK")
