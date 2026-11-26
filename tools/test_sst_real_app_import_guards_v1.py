#!/usr/bin/env python3
"""Pré-verificação específica das incompatibilidades reais detectadas em CI."""
from pathlib import Path
import tempfile
import shutil

repo = Path(__file__).resolve().parents[1]
widget = (repo / 'feature_sources/sst_risk_docs_widget_smoke_test_v1.dart').read_text(encoding='utf-8')
patch = (repo / 'tools/patch_android_standard_conclusion_v1.py').read_text(encoding='utf-8')
source = (repo / 'feature_sources/auditar_unified_conclusion_test_v1.dart').read_text(encoding='utf-8')
assert "final company = Company(" in widget
assert "const company = Company(" not in widget
assert widget.count('await tester.pumpWidget(MaterialApp(') >= 2
assert "test_source=test.read_text" in patch
assert "import '../lib/services/auditar_unified_conclusion.dart';" in patch
assert "old_import=" in patch
assert "import 'auditar_unified_conclusion_v1.dart';" in source
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    target = root / 'test' / 'auditar_unified_conclusion_test.dart'
    target.parent.mkdir(parents=True)
    shutil.copyfile(repo / 'feature_sources/auditar_unified_conclusion_test_v1.dart', target)
    raw = target.read_text(encoding='utf-8')
    old = "import 'auditar_unified_conclusion_v1.dart';"
    assert raw.count(old) == 1
    target.write_text(raw.replace(old, "import '../lib/services/auditar_unified_conclusion.dart';", 1), encoding='utf-8', newline='\n')
    assert "../lib/services/auditar_unified_conclusion.dart" in target.read_text(encoding='utf-8')
print("SST_REAL_APP_IMPORT_GUARDS_OK")
