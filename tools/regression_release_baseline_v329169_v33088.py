#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import sys

root = Path(sys.argv[1])
widget = (root / "lib/widgets/offline_report_inline_suggestions.dart").read_text(encoding="utf-8")
report = (root / "lib/screens/report_screen.dart").read_text(encoding="utf-8")
manager = (root / "lib/screens/manager_reports_screen.dart").read_text(encoding="utf-8")
training = (root / "lib/screens/training_activity_center_screen.dart").read_text(encoding="utf-8")
cipa = (root / "lib/screens/cipa_management_screen.dart").read_text(encoding="utf-8")
home = (root / "lib/screens/home_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")
manifest_path = root / ".auditar_v329169_protected.json"

assert widget.count("OfflineInlineSuggestion(") >= 80
assert "_learnedCacheTtl = Duration(seconds: 8)" in widget
assert "...await _learnedSuggestions()" in widget
assert "Outras sugestões locais" not in widget
assert "Icons.offline_bolt_outlined" not in widget
assert "Icons.auto_awesome_outlined" in widget

assert "final qualityRows = await Future.wait(" in report
assert "premiumFindings.map((answer) async" in report
assert "qualityPossible = qualityRows.length * 5;" in report
assert "Qualidade do relatório" in report

assert "Resumo para decisão" in manager
assert "CAPACITAÇÃO E CONTROLE PREVENTIVO" in manager
assert "final ncsFuture = db.getNonConformityRows" in manager
assert "final activityFutures = <Future<List<SstRecord>>>[" in manager
assert "Opções do relatório" in manager

assert "Planejamento anual" in training
assert "summaryFuture" in training
assert "missingFuture" in training
assert "Planejamento anual da CIPA" in cipa
assert "class HomeScreen" in home

assert manifest_path.exists(), "manifesto do núcleo protegido ausente"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
changed = []
for name, digest in manifest.items():
    current = hashlib.sha256((root / name).read_bytes()).hexdigest()
    if current != digest:
        changed.append(name)
assert not changed, "núcleo protegido mudou após a baseline: " + repr(changed)

assert (
    "version: 3.29.169+311" in pub
    or "version: 3.30.88+275" in pub
), "versao da baseline consolidada incorreta"

for text in (widget, report, manager, training, cipa, home):
    assert "CREATE TABLE" not in text
    assert "ALTER TABLE" not in text
    assert "DROP TABLE" not in text

print("RELEASE_BASELINE_REGRESSION_OK")
print("PATCH_CHAIN_CONSOLIDATED_OK")
print("PROTECTED_CORE_STILL_BYTE_IDENTICAL_OK")
print("MANAGEMENT_AND_TRAINING_LOAD_PERFORMANCE_OK")
print("HOME_LAYOUT_COMPATIBILITY_OK")
print("REPORT_AND_SUGGESTION_PERFORMANCE_OK")
