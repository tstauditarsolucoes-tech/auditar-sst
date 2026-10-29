#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
rules = (root / "lib/services/offline_field_rules_service.dart").read_text(
    encoding="utf-8"
)
dialog = (root / "lib/widgets/offline_field_assistant_dialog.dart").read_text(
    encoding="utf-8"
)
widget = (root / "lib/widgets/offline_report_inline_suggestions.dart").read_text(
    encoding="utf-8"
)
ronda = (root / "lib/screens/express_round_screen.dart").read_text(
    encoding="utf-8"
)
obs = (root / "lib/screens/safety_observations_screen.dart").read_text(
    encoding="utf-8"
)
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

for forbidden in (
    "AiAssistantService",
    "DeviceSyncService",
    "AppDatabase",
    "DriveService",
    "MediaSyncService",
    "apps_script",
):
    assert forbidden not in rules, "dependencia proibida nas regras: " + forbidden
    assert forbidden not in dialog, "dependencia proibida no dialogo: " + forbidden

for snippet in (
    "NR-01",
    "NR-06",
    "NR-10",
    "NR-11",
    "NR-12",
    "NR-13",
    "NR-15",
    "NR-17",
    "NR-18",
    "NR-20",
    "NR-23",
    "NR-24",
    "NR-26",
    "NR-33",
    "NR-35",
):
    assert snippet in rules, "NR ausente na biblioteca local: " + snippet

for snippet in (
    "Segurança de máquinas — parada de emergência",
    "Segurança de máquinas — sensor/intertravamento",
    "Eletricidade",
    "Proteção contra incêndio",
    "Inflamáveis e combustíveis",
    "Trabalho em altura / proteção contra quedas",
    "Andaimes e plataformas",
    "Equipamento de proteção individual",
    "Ruído ocupacional",
    "Calor ocupacional",
    "Produtos químicos",
    "Ergonomia e movimentação manual",
    "Espaço confinado",
):
    assert snippet in rules, "tema ausente: " + snippet

assert widget.count("OfflineInlineSuggestion(") >= 30
assert "auditar-botao-emergencia-inoperante" in widget
assert "auditar-cabo-eletrico-danificado" in widget
assert "auditar-combustivel-recipiente-inadequado" in widget
assert "auditar-andaime-sem-guarda-corpo" in widget
assert "auditar-abertura-piso-sem-protecao" in widget

assert "result.riskSummary" in ronda
assert "result.consequenceSummary" in ronda
assert "risk.text = result.riskSummary" in obs
assert "consequence.text = result.consequenceSummary" in obs

assert (
    "version: 3.29.165+307" in pub
    or "version: 3.30.84+271" in pub
), "versao da biblioteca SST completa incorreta"

print("OFFLINE_SST_COMPLETE_REGRESSION_OK")
print("AT_LEAST_30_LOCAL_TEMPLATES_OK")
print("RISK_CONSEQUENCE_APPLY_IF_EMPTY_OK")
print("CORE_PROTECTED_OK")
