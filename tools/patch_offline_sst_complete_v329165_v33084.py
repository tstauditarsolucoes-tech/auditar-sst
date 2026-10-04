#!/usr/bin/env python3
"""Auditar SST v3.29.165 / v3.30.84 — assistente offline técnico ampliado.

- amplia a biblioteca local de achados;
- melhora classificação por tema;
- detalha risco, consequência, NR, ação, responsável, prazo e evidência;
- sugere P/S inicial editável para a matriz;
- reaproveita risco/consequência nos campos já existentes quando vazios.

Sem schema, sync, auth, HTTP, mídia/Drive, IA, Apps Script ou renderer.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_offline_sst_complete_v329165_v33084.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo = Path(__file__).resolve().parents[1]
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")


def read(rel):
    return (root / rel).read_text(encoding="utf-8")


def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")


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
        "feature_sources/offline_report_inline_suggestions_v329165.dart",
        "lib/widgets/offline_report_inline_suggestions.dart",
    ),
    (
        "feature_sources/offline_field_rules_service_v329165.dart",
        "lib/services/offline_field_rules_service.dart",
    ),
    (
        "feature_sources/offline_field_assistant_dialog_v329165.dart",
        "lib/widgets/offline_field_assistant_dialog.dart",
    ),
    (
        "feature_sources/offline_report_inline_suggestions_test_v329165.dart",
        "test/offline_report_inline_suggestions_test.dart",
    ),
    (
        "feature_sources/offline_field_rules_test_v329165.dart",
        "test/offline_field_rules_test.dart",
    ),
]
for source, target in copies:
    src = repo / source
    dst = root / target
    if not src.exists():
        raise RuntimeError("fonte ausente: " + source)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)

# Registro técnico: preenche apenas campos vazios.
rel = "lib/screens/safety_observations_screen.dart"
s = read(rel)
old = """      if (recommendation.text.trim().isEmpty) {
        recommendation.text = result.actionPlan;
      }
"""
new = """      if (risk.text.trim().isEmpty && result.riskSummary.trim().isNotEmpty) {
        risk.text = result.riskSummary;
      }
      if (consequence.text.trim().isEmpty &&
          result.consequenceSummary.trim().isNotEmpty) {
        consequence.text = result.consequenceSummary;
      }
      if (recommendation.text.trim().isEmpty) {
        recommendation.text = result.actionPlan;
      }
"""
if new not in s:
    if s.count(old) != 1:
        raise RuntimeError(
            "registro tecnico: bloco de aplicacao esperado 1 vez, encontrado "
            + str(s.count(old))
        )
    s = s.replace(old, new, 1)
write(rel, s)

# Ronda: reaproveita risco/consequência locais sem sobrescrever modelo selecionado.
rel = "lib/screens/express_round_screen.dart"
s = read(rel)
old = """      if (offlineModelRecommendation.trim().isEmpty) {
        offlineModelRecommendation = result.actionPlan;
      }
"""
new = """      if (offlineModelRisk.trim().isEmpty &&
          result.riskSummary.trim().isNotEmpty) {
        offlineModelRisk = result.riskSummary;
      }
      if (offlineModelConsequence.trim().isEmpty &&
          result.consequenceSummary.trim().isNotEmpty) {
        offlineModelConsequence = result.consequenceSummary;
      }
      if (offlineModelRecommendation.trim().isEmpty) {
        offlineModelRecommendation = result.actionPlan;
      }
"""
if new not in s:
    if s.count(old) != 1:
        raise RuntimeError(
            "Ronda: bloco de aplicacao esperado 1 vez, encontrado "
            + str(s.count(old))
        )
    s = s.replace(old, new, 1)
write(rel, s)

# Versão.
pub_path = root / "pubspec.yaml"
pub = pub_path.read_text(encoding="utf-8")
old_version, new_version = (
    ("3.29.164+306", "3.29.165+307")
    if platform == "android"
    else ("3.30.83+270", "3.30.84+271")
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

rules = read("lib/services/offline_field_rules_service.dart")
dialog = read("lib/widgets/offline_field_assistant_dialog.dart")
widget = read("lib/widgets/offline_report_inline_suggestions.dart")
ronda = read("lib/screens/express_round_screen.dart")
obs = read("lib/screens/safety_observations_screen.dart")

for snippet in (
    "riskSummary",
    "consequenceSummary",
    "evidenceSuggestion",
    "nrDetails",
    "suggestedProbabilityForText",
    "suggestedSeverityForText",
    "Segurança de máquinas — parada de emergência",
    "Espaço confinado",
    "Equipamentos pressurizados",
):
    assert snippet in rules, "regra ampliada ausente: " + snippet

for snippet in (
    "Análise técnica sem IA",
    "Risco identificado",
    "Consequência possível",
    "Base normativa sugerida",
    "Evidência recomendada para encerramento",
):
    assert snippet in dialog, "dialogo ampliado ausente: " + snippet

assert "auditar-cabo-eletrico-danificado" in widget
assert "auditar-andaime-sem-ancoragem" in widget
assert "auditar-quimico-sem-identificacao" in widget
assert "auditar-postura-inadequada" in widget
assert "auditar-poeira-sem-protecao" in widget
assert "result.riskSummary" in ronda
assert "result.consequenceSummary" in ronda
assert "risk.text = result.riskSummary" in obs
assert "consequence.text = result.consequenceSummary" in obs
assert "version: " + new_version in pub_path.read_text(encoding="utf-8")

print("OFFLINE_SST_COMPLETE_OK", platform, new_version)
print("MACHINE_ELECTRICAL_FIRE_HEIGHT_PPE_CHEMICAL_ERGO_LIBRARY_OK")
print("RISK_CONSEQUENCE_NR_ACTION_OWNER_DEADLINE_EVIDENCE_OK")
print("NO_SCHEMA_SYNC_AUTH_HTTP_MEDIA_DRIVE_AI_GS_REPORT_CHANGE_OK")
