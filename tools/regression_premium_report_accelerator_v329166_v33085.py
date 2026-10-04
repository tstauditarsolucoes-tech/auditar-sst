#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
widget = (root / "lib/widgets/offline_report_inline_suggestions.dart").read_text(encoding="utf-8")
ronda = (root / "lib/screens/express_round_screen.dart").read_text(encoding="utf-8")
report = (root / "lib/screens/report_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

assert widget.count("OfflineInlineSuggestion(") >= 80
for required in (
    "auditar-saida-emergencia-obstruida",
    "auditar-esmerilhadeira-sem-protecao",
    "auditar-empilhadeira-sem-cinto",
    "auditar-gancho-sem-trava",
    "auditar-escavacao-sem-escoramento",
    "auditar-cilindro-gas-sem-fixacao",
    "auditar-ventilacao-inadequada",
    "auditar-iluminacao-insuficiente",
):
    assert required in widget, "modelo premium ausente: " + required

assert "'sem internet'" not in widget
assert "Sugestões mais próximas" in widget
assert "Nenhum modelo semelhante encontrado" in widget
assert "contextConcepts" in widget
assert "_roundReportQualityScore" in ronda
assert "Conferir para um relatório mais completo" in ronda
assert "reportQualityScore" in report
assert "Qualidade do relatório" in report
assert "_reviewReportWithAi" in report
assert "IA texto" in ronda
for forbidden in ("CREATE TABLE", "ALTER TABLE"):
    assert forbidden not in widget
assert (
    "version: 3.29.166+308" in pub
    or "version: 3.30.85+272" in pub
), "versao premium incorreta"

print("PREMIUM_REPORT_ACCELERATOR_REGRESSION_OK")
print("SUGGESTION_LIBRARY_80_PLUS_OK")
print("SEM_INTERNET_LABEL_REMOVED_OK")
print("QUALITY_REVIEW_NON_BLOCKING_OK")
print("AI_PATHS_PRESERVED_OK")
