#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
renderer = (root / "lib/services/ronda_standard3_pdf_service.dart").read_text(
    encoding="utf-8"
)
ai = (root / "lib/services/ai_assistant_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

normalized = "".join(renderer.split())

for snippet in (
    "RELATÓRIO DE VISTORIA TÉCNICA",
    "IDENTIFICAÇÃO DA EMPRESA",
    "_logo(companyLogo, 82, 58)",
    "flex: 48",
    "flex: 52",
    "fontSize: 10.2",
    "fontSize: 8.7",
    "_compactTitle",
    "_compactReferences",
    "exigências aplicáveis do Corpo de Bombeiros",
):
    assert snippet in renderer, "regressao visual Ronda: " + snippet

assert "AppDatabase.instance.getCompanies" in renderer
assert "onlyActive" in renderer
assert (
    "_logo(auditarLogo, 104, 56)" in renderer
    or "_auditarBrand(auditarLogo, 112, 58)" in renderer
    or "_auditarBrand(auditarLogo, 122, 59)" in renderer
)
assert (
    "_logo(auditarLogo, 90, 34)" in renderer
    or "_auditarBrand(auditarLogo, 92, 42)" in renderer
    or "_auditarBrand(auditarLogo, 95, 46)" in renderer
)
assert "companyLogo ?? auditarLogo" not in renderer
assert ai.count("'mode': 'checklist_photo'") >= 2
assert "'rondaDeferred': false" in ai
assert "'rondaDeferred': true" in ai
assert (
    "version: 3.29.154+296" in pub
    or "version: 3.29.155+297" in pub
    or "version: 3.30.73+260" in pub
    or "version: 3.30.74+261" in pub
)

print("RONDA_VISUAL_PARITY_REGRESSION_OK")
print("AI_FLOW_PRESERVED_OK")
