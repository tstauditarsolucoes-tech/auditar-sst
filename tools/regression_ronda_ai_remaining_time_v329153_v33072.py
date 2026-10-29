#!/usr/bin/env python3
"""Regressao da estimativa visual de tempo restante da IA da Ronda."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit(
        "uso: regression_ronda_ai_remaining_time_v329153_v33072.py <APP_DIR>"
    )

root = Path(sys.argv[1])
ronda = (root / "lib/screens/express_round_screen.dart").read_text(
    encoding="utf-8"
)
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

for snippet in (
    "Timer? _aiPhotoTimer;",
    "_aiPhotoElapsedSeconds",
    "static const int _aiPhotoEstimatedSeconds = 50;",
    "final remaining = _aiPhotoEstimatedSeconds - _aiPhotoElapsedSeconds;",
    "IA analisando foto • ~${remaining}s restantes",
    "IA finalizando análise...",
    "Timer.periodic(const Duration(seconds: 1)",
):
    assert snippet in ronda, "Ronda remaining-time regression missing: " + snippet

assert "IA analisando foto • ${_aiPhotoElapsedSeconds}s" not in ronda
assert (
    "version: 3.29.153+295" in pub
    or "version: 3.30.72+259" in pub
)

print("RONDA_AI_REMAINING_TIME_REGRESSION_OK")
