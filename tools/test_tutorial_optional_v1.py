#!/usr/bin/env python3
"""Regressão do mini tutorial opcional Auditar SST (sem acesso a dados)."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("app/Auditar_SST_v1_5_dashboard")
bubble = (root / "lib/widgets/tutorial_bubble.dart").read_text(encoding="utf-8")
service = (root / "lib/services/tutorial_service.dart").read_text(encoding="utf-8")
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
settings = (root / "lib/screens/settings_screen.dart").read_text(encoding="utf-8")

ids = re.findall(r"^    '([a-z_]+)': TutorialContent\(", bubble, flags=re.M)
expected = {
    "home", "companies", "company_detail", "field_quick", "history",
    "non_conformities", "action_plan", "workers", "trainings",
    "compliance_alerts", "cipa", "checklists", "routine", "improvements",
    "dashboard", "new_inspection", "settings",
}
assert set(ids) == expected, f"mudança indesejada nos módulos: {set(ids) ^ expected}"
assert len(ids) == 17 and len(set(ids)) == 17

for text in (
    "Pular tutorial", "Parar dicas", "TutorialService.disableAll()",
    "TutorialService.markSeen(tutorialId)", "showIfNeeded",
    "class TutorialScreenShell", "barrierDismissible: false",
):
    assert text in bubble, f"faltou comportamento original: {text}"
for text in ("showGuide(", "_TutorialGuideCenter", "Guia de uso do Auditar SST"):
    assert text not in bubble, f"guia separado foi reintroduzido: {text}"

assert "tutorialVersion = '1'" in service
assert "_disabledKey" in service and "if (disabled == 'true') return false;" in service
assert "resetForCurrentAccount()" in service
assert "tooltip: 'Ajuda rápida'" in home
assert "Novidades do app" not in home
assert "Reiniciar mini tutorial" in settings
assert "Abrir guia completo do app" not in settings

for phrase in (
    "Linha do tempo", "Proteção removida", "Extintor vencido",
    "Visita rápida", "cliente", "NR-18", "rascunho", "PDF",
):
    assert phrase.lower() in bubble.lower(), f"explicação nova não encontrada: {phrase}"

sections = re.findall(
    r"^    '([a-z_]+)': TutorialContent\((.*?)^    \),",
    bubble, flags=re.M | re.S
)
assert len(sections) == 17, f"não foi possível ler os 17 assuntos: {len(sections)}"
for key, content in sections:
    assert "title:" in content and "description:" in content
    assert len(re.findall(r"^        '", content, flags=re.M)) == 3, (
        f"esperadas 3 dicas curtas em {key}"
    )

print("TUTORIAL_OPCIONAL_OK: 17 áreas, conteúdo revisado e experiência original preservada")
