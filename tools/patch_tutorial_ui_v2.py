#!/usr/bin/env python3
"""Integra o guia de uso no final da montagem do app, após patches históricos.

Alteração de interface apenas: Home e Configurações. Não toca em banco,
autenticação, sincronização, PDFs, mídia, GS ou demais recursos.
"""
from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("app/Auditar_SST_v1_5_dashboard")
home = root / "lib/screens/home_screen.dart"
settings = root / "lib/screens/settings_screen.dart"
widget = root / "lib/widgets/tutorial_bubble.dart"
assert all(p.is_file() for p in (home, settings, widget)), "arquivos do tutorial ausentes"

protected = [
    root / "lib/database.dart",
    root / "lib/services/auth_service.dart",
    root / "lib/services/device_sync_service.dart",
    root / "lib/services/sync_coordinator.dart",
    root / "lib/services/media_sync_service.dart",
    root / "lib/services/drive_service.dart",
]
before = {
    p: hashlib.sha256(p.read_bytes()).hexdigest()
    for p in protected if p.is_file()
}

def replace_one(text: str, old: str, new: str, label: str) -> str:
    assert text.count(old) == 1, f"{label}: encontrado {text.count(old)} vez(es)"
    return text.replace(old, new, 1)

h = home.read_text(encoding="utf-8")
assert "TutorialCoach" in h, "a Home deve carregar o mini tutorial original"
assert "Novidades do app" not in h, "não duplicar o atalho de novidades"
old = """          IconButton(
            tooltip: 'Ajuda rápida',
            onPressed: () => TutorialCoach.show(context, 'home', force: true),
            icon: const Icon(Icons.help_outline_rounded),
          ),"""
new = """          IconButton(
            tooltip: 'Guia de uso',
            onPressed: () => TutorialCoach.showGuide(context),
            icon: const Icon(Icons.help_outline_rounded),
          ),
          IconButton(
            tooltip: 'Novidades do app',
            onPressed: () => TutorialCoach.show(
              context, 'latest_features', force: true,
            ),
            icon: const Icon(Icons.new_releases_outlined),
          ),"""
h = replace_one(h, old, new, "atalho guia na Home")

s = settings.read_text(encoding="utf-8")
assert "TutorialService.resetForCurrentAccount" in s, "reinício de dicas original ausente"
assert "Abrir guia completo do app" not in s, "não duplicar botão no painel"
s = replace_one(
    s,
    "import '../services/tutorial_service.dart';",
    "import '../services/tutorial_service.dart';\nimport '../widgets/tutorial_bubble.dart';",
    "import guia em Configurações",
)
s = replace_one(
    s,
    "'O aplicativo mostra uma dica curta na primeira vez que cada área é aberta. O tutorial pode ser pulado a qualquer momento.'",
    "'O aplicativo explica as funções com passos simples. Use o Guia de uso para consultar os assuntos quando precisar.'",
    "descrição do guia",
)
s = replace_one(
    s,
    """                  OutlinedButton.icon(
                    onPressed: _resetTutorial,""",
    """                  FilledButton.icon(
                    onPressed: () => TutorialCoach.showGuide(context),
                    icon: const Icon(Icons.menu_book_outlined),
                    label: const Text('Abrir guia completo do app'),
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: _resetTutorial,""",
    "botão guia em Configurações",
)

assert "class _TutorialGuideCenter" in widget.read_text(encoding="utf-8")
home.write_text(h, encoding="utf-8", newline="\n")
settings.write_text(s, encoding="utf-8", newline="\n")

for p, digest in before.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, f"arquivo protegido alterado: {p}"
assert "TutorialCoach.showGuide(context)" in h
assert "TutorialCoach.showGuide(context)" in s
print("TUTORIAL_V2_READY: guia na Home e Configurações; arquivos protegidos preservados.")
