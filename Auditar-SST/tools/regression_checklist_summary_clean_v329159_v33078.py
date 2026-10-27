#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
styled = (root / "lib/services/styled_report_pdf_service.dart").read_text(encoding="utf-8")
checklist = (root / "lib/screens/checklist_screen.dart").read_text(encoding="utf-8")
models = (root / "lib/models.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

start = styled.find("  static pw.Widget _issueBlock(")
end = styled.find("  static pw.Widget _photos(", start)
assert start >= 0 and end > start, "card-resumo nao localizado"
block = styled[start:end]

assert "_labelValue('Risco', risk)" not in block
assert "_priorityChip(priority)" not in block
for marker in (
    "_labelValue('Situação encontrada', problem)",
    "_labelValue('Correção recomendada', recommendation)",
    "_labelValue('Referência', reference)",
):
    assert marker in block, "campo essencial removido do resumo: " + marker

assert "riskIdentified" in models
assert "classification" in models
assert "Risco identificado" in checklist
assert (
    "Classificação / prioridade da NC" in checklist
    or "Prioridade informada pelo técnico" in checklist
), "campo de prioridade do cadastro foi removido"

assert (
    "version: 3.29.159+301" in pub
    or "version: 3.30.78+265" in pub
), "versao do resumo limpo incorreta"

print("CHECKLIST_SUMMARY_CLEAN_REGRESSION_OK")
print("RISK_AND_PRIORITY_NOT_RENDERED_IN_SHORT_CARD_OK")
print("UNDERLYING_RISK_CLASSIFICATION_DATA_PRESERVED_OK")
print("CHECKLIST_ENTRY_FIELDS_PRESERVED_OK")
