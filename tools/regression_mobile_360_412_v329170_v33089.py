#!/usr/bin/env python3
"""Regressão do ajuste responsivo v3.29.170 / v3.30.89."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_mobile_360_412_v329170_v33089.py <APP_DIR>")

root = Path(sys.argv[1])
screen = (root / "lib/screens/extinguisher_monthly_inspection_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

assert "MediaQuery.sizeOf(context).width <= 412 ? 3 : 4" in screen
assert "gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(" not in screen
assert "childAspectRatio: 1.35" in screen
assert "maxLines: 2" in screen
assert "overflow: TextOverflow.ellipsis" in screen
assert "textAlign: TextAlign.center" in screen
assert (
    "version: 3.29.170+312" in pub
    or "version: 3.30.89+276" in pub
)

print("MOBILE_360_412_REGRESSION_OK")
print("EXTINGUISHER_YEAR_HISTORY_RESPONSIVE_OK")
