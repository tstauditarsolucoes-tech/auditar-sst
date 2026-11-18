#!/usr/bin/env python3
"""Regressão: instalação Android deve falhar sem alterar arquivo algum.

Executa apenas com dados fictícios e diretório temporário. Não requer Flutter,
credenciais, servidor nem aplicativo real.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "tools/patch_android_unified_visits_v1.py"

QUICK = """import 'express_round_screen.dart';
    this.onSelected,
  });
  final ValueChanged<Company>? onSelected;
          _action(
            'Nova ronda',
            'Fotos e descrição das situações encontradas',
            Icons.add_a_photo_outlined,
            ExpressRoundScreen(company: c),
          ),
          _action(
            'Nova vistoria',
            'Inspeção com checklist da empresa selecionada',
            Icons.fact_check_outlined,
            NewInspectionScreen(initialCompany: c, fieldMode: true),
          ),
"""
# Deliberadamente falta _refresh: a versão confere, mas a estrutura da
# Home está incompatível. Isso precisa falhar antes de gerar qualquer arquivo.
HOME = """import '../services/device_sync_service.dart';
import 'quick_visit_screen.dart';
"""

def exercise(version: str, label: str) -> None:
    with tempfile.TemporaryDirectory(prefix="auditar_preflight_") as tmp:
        app = Path(tmp)
        screens = app / "lib/screens"
        screens.mkdir(parents=True)
        quick = screens / "quick_visit_screen.dart"
        home = screens / "home_screen.dart"
        pub = app / "pubspec.yaml"
        quick.write_text(QUICK, encoding="utf-8")
        home.write_text(HOME, encoding="utf-8")
        pub.write_text(f"name: auditar_sst\nversion: {version}\n", encoding="utf-8")
        original = {path: path.read_bytes() for path in (quick, home, pub)}
        result = subprocess.run(
            [sys.executable, str(PATCH), str(app)],
            capture_output=True, text=True, check=False, timeout=15,
        )
        assert result.returncode != 0, f"{label}: patch deveria interromper"
        for path, data in original.items():
            assert path.read_bytes() == data, f"{label}: arquivo alterado: {path}"
        for path in (
            screens / "visit_type_chooser_screen.dart",
            screens / "smart_visit_briefing_screen.dart",
            app / "lib/services/unified_visit_metrics.dart",
            app / "lib/services/visit_intelligence.dart",
        ):
            assert not path.exists(), f"{label}: instalação parcial: {path}"

if __name__ == "__main__":
    exercise("3.29.999+999", "versão não autorizada")
    exercise("3.29.200+342", "Home incompatível")
    print("PREFLIGHT_ANDROID_2_CENARIOS_SEM_ALTERACOES_OK")
