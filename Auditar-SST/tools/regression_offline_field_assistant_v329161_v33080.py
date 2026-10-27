#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])

rules = (root / "lib/services/offline_field_rules_service.dart").read_text(encoding="utf-8")
dialog = (root / "lib/widgets/offline_field_assistant_dialog.dart").read_text(encoding="utf-8")
observation = (root / "lib/screens/safety_observations_screen.dart").read_text(encoding="utf-8")
round_screen = (root / "lib/screens/express_round_screen.dart").read_text(encoding="utf-8")
checklist = (root / "lib/screens/checklist_screen.dart").read_text(encoding="utf-8")
report = (root / "lib/screens/report_screen.dart").read_text(encoding="utf-8")
ai = (root / "lib/services/ai_assistant_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

for forbidden in (
    "AiAssistantService",
    "apps_script",
    "DeviceSyncService",
    "AppDatabase",
    "DriveService",
    "MediaSyncService",
):
    assert forbidden not in rules, "dependencia proibida nas regras offline: " + forbidden

for snippet in (
    "suggestNrs",
    "priorityFromMatrix",
    "matrixScore",
    "buildActionPlan",
    "suggestDeadline",
    "NR-06",
    "NR-10",
    "NR-12",
    "NR-23",
    "NR-35",
):
    assert snippet in rules, "regra offline ausente: " + snippet

assert "Não usa internet nem IA" in dialog
assert "Probabilidade (1 a 5)" in dialog
assert "Severidade (1 a 5)" in dialog
assert "Situação recorrente" in dialog

o_start = observation.index("  Future<void> _openOfflineFieldAssistant()")
o_end = observation.index("  Future<void> _useOfflineTemplate()", o_start)
o_block = observation[o_start:o_end]
assert "AiAssistantService" not in o_block
assert "OfflineReportInlineSuggestionService.search" in o_block
assert "item.learned || item.useCount > 0" in o_block
assert "recommendation.text = result.actionPlan" in o_block
assert "priority = result.priority" in o_block
assert "Abrir assistente sem IA" in observation

r_start = round_screen.index("  Future<void> _openRoundOfflineAssistant()")
r_end = round_screen.index("  void _applyOfflineRoundSuggestion", r_start)
r_block = round_screen[r_start:r_end]
assert "AiAssistantService" not in r_block
assert "OfflineReportInlineSuggestionService.search" in r_block
assert "offlineModelRecommendation = result.actionPlan" in r_block
assert "Matriz e NR sem IA" in round_screen

c_start = checklist.index("  Future<void> _openFastOfflineAssistant()")
c_end = checklist.index("  Widget _fastCaptureCard()", c_start)
c_block = checklist[c_start:c_end]
assert "AiAssistantService" not in c_block
assert "_fastPriority = result.priority" in c_block
assert "Calcular prioridade e NR sem IA" in checklist

s_start = report.index("  String _buildOfflineExecutiveSummary()")
s_end = report.index("  String _buildOfflineInspectionConclusion()", s_start)
s_block = report[s_start:s_end]
assert "AiAssistantService" not in s_block
assert "updateInspectionNarrative" in s_block
assert "Resumo executivo — sem IA" in report
assert "Gerar resumo sem IA" in report

# Rotas existentes de IA continuam disponíveis.
assert "AiAssistantService.reviewExpressRound" in round_screen
assert "AiAssistantService.reviewFinalReport" in report
assert ai.count("'mode': 'checklist_photo'") >= 2
assert "'rondaDeferred': false" in ai
assert "'rondaDeferred': true" in ai

assert (
    "version: 3.29.161+303" in pub
    or "version: 3.30.80+267" in pub
), "versao do assistente offline incorreta"

print("OFFLINE_FIELD_ASSISTANT_REGRESSION_OK")
print("NO_AI_CALL_IN_LOCAL_RULES_OK")
print("LOCAL_HISTORY_RECURRENCE_HINT_OK")
print("EXISTING_AI_PATHS_PRESERVED_OK")
print("NO_SYNC_DB_SCHEMA_AUTH_HTTP_MEDIA_DRIVE_GS_CHANGE_REQUIRED_OK")
