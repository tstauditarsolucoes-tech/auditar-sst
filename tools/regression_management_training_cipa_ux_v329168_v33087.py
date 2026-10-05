#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import sys

root = Path(sys.argv[1])
manager = (root / "lib/screens/manager_reports_screen.dart").read_text(encoding="utf-8")
training = (root / "lib/screens/training_activity_center_screen.dart").read_text(encoding="utf-8")
cipa = (root / "lib/screens/cipa_management_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")
manifest_path = root / ".auditar_v329168_protected.json"

assert "Resumo para decisão" in manager
assert "CAPACITAÇÃO E CONTROLE PREVENTIVO" in manager
assert "missingRequiredTrainingCount" in manager
assert "Opções do relatório" in manager
assert "Pesquisa específica e fotografias" in manager
assert "Planejamento anual" in training
assert "missingRequiredTrainings" in training
assert "getMissingRequiredTrainings" in training
assert "Planejamento anual da CIPA" in cipa
assert "conferir" in cipa
assert "planejar" in cipa

assert manifest_path.exists(), "manifesto do núcleo protegido ausente"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
changed = []
for name, digest in manifest.items():
    current = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if current != digest:
        changed.append(name)
assert not changed, "núcleo protegido mudou após o patch: " + repr(changed)

assert (
    "version: 3.29.168+310" in pub
    or "version: 3.30.87+274" in pub
), "versao de gestao/UX incorreta"

for text in (manager, training, cipa):
    assert "CREATE TABLE" not in text
    assert "ALTER TABLE" not in text
    assert "DROP TABLE" not in text

print("MANAGEMENT_TRAINING_CIPA_UX_REGRESSION_OK")
print("PROTECTED_CORE_STILL_BYTE_IDENTICAL_OK")
print("MANAGEMENT_DECISION_VIEW_OK")
print("TRAINING_ANNUAL_PREVENTION_OK")
print("CIPA_ANNUAL_PLANNING_OK")
print("UI_SIMPLIFICATION_OK")
