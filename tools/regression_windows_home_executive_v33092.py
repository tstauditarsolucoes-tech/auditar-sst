#!/usr/bin/env python3
"""Regressão visual/estrutural Home Windows v3.30.92."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_windows_home_executive_v33092.py <APP_DIR>")

root = Path(sys.argv[1])
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

checks = {
    "version": "version: 3.30.92+279" in pub,
    "desktop_layout_routed": "LayoutBuilder" in home and "_desktopBody()" in home and "_mobileBody()" in home,
    "desktop_method": "Widget _desktopBody()" in home,
    "mobile_preserved": "Widget _mobileBody()" in home,
    "hero": "CENTRAL EXECUTIVA AUDITAR SST" in home,
    "hero_copy": "Gestão SST em uma visão única" in home,
    "management_button": "Abrir Central de Gestão" in home,
    "executive_nav": "Painel executivo" in home,
    "tags": all(x in home for x in [
        "Painel Executivo", "Evolução mensal", "Antes × Depois", "Prioridades"
    ]),
    "management_route": "FieldOperationalControlScreen" in home,
}
failed = [k for k, v in checks.items() if not v]
if failed:
    raise AssertionError("regressão Home Executiva: " + repr(failed))

print("WINDOWS_HOME_EXECUTIVE_REGRESSION_OK")
print("MOBILE_LAYOUT_PATH_STILL_PRESENT_OK")
