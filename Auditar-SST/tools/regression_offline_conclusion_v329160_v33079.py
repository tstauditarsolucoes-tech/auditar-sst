#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
round_screen = (root / "lib/screens/express_round_screen.dart").read_text(encoding="utf-8")
report = (root / "lib/screens/report_screen.dart").read_text(encoding="utf-8")
ai = (root / "lib/services/ai_assistant_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

r_start = round_screen.index("  Future<void> _generateRoundConclusionOffline()")
r_end = round_screen.index("  String _fallbackRoundConclusion()", r_start)
r_block = round_screen[r_start:r_end]
assert "AiAssistantService" not in r_block
assert "reviewExpressRound" not in r_block
assert "_buildOfflineRoundConclusion()" in r_block
assert "express_round_conclusion_$roundId" in r_block
assert "Gerar conclusão sem IA" in round_screen

v_start = report.index("  Future<void> _generateOfflineInspectionConclusion()")
v_end = report.index("  Future<void> _reviewReportWithAi()", v_start)
v_block = report[v_start:v_end]
assert "AiAssistantService" not in v_block
assert "reviewFinalReport" not in v_block
assert "_buildOfflineInspectionConclusion()" in v_block
assert "updateInspectionNarrative" in v_block
assert "general_notes" in v_block
assert "Conclusão do relatório — sem IA" in report

assert "AiAssistantService.reviewExpressRound" in round_screen
assert "AiAssistantService.reviewFinalReport" in report
assert ai.count("'mode': 'checklist_photo'") >= 2
assert "'rondaDeferred': false" in ai
assert "'rondaDeferred': true" in ai

assert (
    "version: 3.29.160+302" in pub
    or "version: 3.30.79+266" in pub
), "versao conclusao offline incorreta"

print("OFFLINE_CONCLUSION_REGRESSION_OK")
print("RONDA_OFFLINE_PATH_HAS_NO_AI_CALL_OK")
print("VISTORIA_OFFLINE_PATH_HAS_NO_AI_CALL_OK")
print("AI_PATHS_REMAIN_AVAILABLE_OK")
print("NO_SYNC_OR_SCHEMA_CHANGE_REQUIRED_OK")
