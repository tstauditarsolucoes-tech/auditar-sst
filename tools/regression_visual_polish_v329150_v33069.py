#!/usr/bin/env python3
"""Regressão das correções visuais v3.29.150 / v3.30.69."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: regression_visual_polish_v329150_v33069.py <APP_DIR>")

root = Path(sys.argv[1])
doc = (root / "lib/screens/document_dispatch_center_screen.dart").read_text(encoding="utf-8")
field = (root / "lib/screens/field_intelligence_center_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

assert "Central de documentos e envios" not in doc
assert "title:const Text('Central de documentos')" in doc
assert "FittedBox" in doc
assert "Text('Histórico de envios')" in doc
assert "onSelected:(_)=>setState(()=>showHistory=true)" in doc
assert "labelColor: Colors.white" in field
assert "unselectedLabelColor: Colors.white70" in field
assert "indicatorColor: Colors.white" in field
assert "text: 'Hoje'" in field
assert "text: 'Busca'" in field
assert "text: 'Evidências'" in field
assert (
    "version: 3.29.150+292" in pub
    or "version: 3.30.69+256" in pub
)

print("VISUAL_POLISH_REGRESSION_OK")
print("DOCUMENT_CENTER_BEHAVIOR_PRESERVED_OK")
print("FIELD_CENTER_TABS_VISIBLE_OK")
