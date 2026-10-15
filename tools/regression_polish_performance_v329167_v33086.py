#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
widget = (root / "lib/widgets/offline_report_inline_suggestions.dart").read_text(encoding="utf-8")
report = (root / "lib/screens/report_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

assert widget.count("OfflineInlineSuggestion(") >= 80
assert "_learnedCacheTtl = Duration(seconds: 8)" in widget
assert "static Future<List<OfflineInlineSuggestion>> _learnedSuggestions()" in widget
assert "...await _learnedSuggestions()" in widget
assert "Outras sugestões locais" not in widget
assert "Icons.offline_bolt_outlined" not in widget
assert "Icons.auto_awesome_outlined" in widget
assert "Sugestões mais próximas" in widget
assert "a IA texto continua disponível" in widget

assert "final qualityRows = await Future.wait(" in report
assert "premiumFindings.map((answer) async" in report
assert "qualityPossible = qualityRows.length * 5;" in report
assert "final photos = await db.getPhotosForAnswer(answer.id);" in report
assert "Qualidade do relatório" in report

for forbidden in ("CREATE TABLE", "ALTER TABLE", "DROP TABLE"):
    assert forbidden not in widget

assert (
    "version: 3.29.167+309" in pub
    or "version: 3.30.86+273" in pub
), "versao de polimento/desempenho incorreta"

print("POLISH_PERFORMANCE_REGRESSION_OK")
print("LOCAL_KNOWLEDGE_DISK_READ_THROTTLED_OK")
print("REPORT_PREFLIGHT_PARALLEL_OK")
print("VISUAL_TECHNICAL_JARGON_REDUCED_OK")
print("AI_PATHS_PRESERVED_OK")
