#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
widget = (root / "lib/widgets/offline_report_inline_suggestions.dart").read_text(
    encoding="utf-8"
)
ronda = (root / "lib/screens/express_round_screen.dart").read_text(
    encoding="utf-8"
)
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

required_widget = (
    "auditar-botao-emergencia-inoperante",
    "Botão de emergência inoperante",
    "machine_control",
    "score -= 24",
    "return score >= 6 ? score : 0",
    "Sugestões mais próximas",
    "items.take(2)",
    "showModalBottomSheet<void>",
    "Ver mais ",
)
for snippet in required_widget:
    assert snippet in widget, "sugestao offline incompleta: " + snippet

assert "Analisar risco e NR sem IA" in ronda
assert "Matriz e NR sem IA" not in ronda

for forbidden in (
    "AiAssistantService",
    "DeviceSyncService",
    "MediaSyncService",
    "DriveService",
    "ALTER TABLE",
    "CREATE TABLE",
):
    assert forbidden not in widget, "dependencia indevida no widget: " + forbidden

assert (
    "version: 3.29.164+306" in pub
    or "version: 3.30.83+270" in pub
), "versao incorreta"

print("RONDA_RELEVANCE_REGRESSION_OK")
print("NO_UNRELATED_EXTINGUISHER_BY_GENERIC_EMERGENCY_WORD_OK")
print("COMPACT_TWO_SUGGESTIONS_PLUS_MORE_OK")
print("NO_CORE_DEPENDENCY_ADDED_OK")
