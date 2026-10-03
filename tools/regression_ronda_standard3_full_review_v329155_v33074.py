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

required = (
    "RELATÓRIO DE VISTORIA TÉCNICA",
    "IDENTIFICAÇÃO DA EMPRESA",
    "seenRecordIds",
    "_captionFromTitle",
    "_compactConclusion",
    "_compactReferences",
    "_auditarBrand",
    "registeredCompany?.logoPath ?? company.logoPath",
    "_logo(companyLogo, 82, 58)",
    "PRIORIDADE:",
    "TÉCNICO EM SEGURANÇA DO TRABALHO",
)
for snippet in required:
    assert snippet in renderer, "regressao Ronda modelo final: " + snippet

assert "AppDatabase.instance.getCompanies(onlyActive:false)" in normalized
assert "companyLogo ?? auditarLogo" not in renderer
assert "VALE DO LEITE" not in renderer.upper()
assert "LATICÍNIOS VALE DO LEITE" not in renderer.upper()
assert renderer.count("_logo(companyLogo, 82, 58)") == 1
assert ai.count("'mode': 'checklist_photo'") >= 2
assert "'rondaDeferred': false" in ai
assert "'rondaDeferred': true" in ai
assert (
    "version: 3.29.155+297" in pub
    or "version: 3.30.74+261" in pub
)

print("RONDA_FINAL_MODEL_REGRESSION_OK")
print("NO_HARDCODED_CLIENT_BRANDING_OK")
print("AI_FLOW_PRESERVED_OK")
