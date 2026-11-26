#!/usr/bin/env python3
"""Regressões rápidas: testes do app real não dependem de fixture fictícia."""
from pathlib import Path
import tempfile
import shutil

repo = Path(__file__).resolve().parents[1]
widget = (repo / 'feature_sources/sst_risk_docs_widget_smoke_test_v1.dart').read_text(encoding='utf-8')
patch = (repo / 'tools/patch_android_standard_conclusion_v1.py').read_text(encoding='utf-8')
installer = (repo / 'tools/patch_sst_report_center_v1.py').read_text(encoding='utf-8')
flutter_test = (repo / 'feature_sources/auditar_unified_conclusion_flutter_test_v1.dart').read_text(encoding='utf-8')

assert "final company = Company(" in widget
assert "const company = Company(" not in widget
assert widget.count('await tester.pumpWidget(MaterialApp(') >= 2
assert "sst_risk_docs_widget_smoke_test.dart" not in installer
assert "auditar_unified_conclusion_flutter_test_v1.dart" in patch
assert "import '../lib/services/auditar_unified_conclusion.dart';" in flutter_test
assert "import 'package:flutter_test/flutter_test.dart';" in flutter_test
assert "test('Conclusão local padrão da Ronda" in flutter_test

with tempfile.TemporaryDirectory() as temp:
    target = Path(temp) / 'test' / 'auditar_unified_conclusion_test.dart'
    target.parent.mkdir(parents=True)
    shutil.copyfile(repo / 'feature_sources/auditar_unified_conclusion_flutter_test_v1.dart', target)
    raw = target.read_text(encoding='utf-8')
    assert raw.count("test('") >= 1
    assert raw.count("../lib/services/auditar_unified_conclusion.dart") == 1
print("SST_REAL_APP_IMPORT_GUARDS_OK")
