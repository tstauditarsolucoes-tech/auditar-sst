#!/usr/bin/env python3
"""Exercise the assembled-navigation regression checker with formatted routes."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
regression = repo/"tools/regression_visit_navigation_v329188_v330111.py"
source = regression.read_text(encoding="utf-8")
assert source.count('r"\\s+"') == 2, "Whitespace regex reverted or changed"
assert re.sub(r"\s+", "", "A(\n   b  )") == "A(b)"
fixture = """
class VisitIntentTabs extends StatelessWidget {}
final chosen=_activeIntent=widget.intent;
final tab=selected:_activeIntent;
final title=switch (_activeIntent) { };
if (_activeIntent == VisitIntent.visit) {}
if (_activeIntent == VisitIntent.drafts) {}
if (_activeIntent == VisitIntent.pending) {}
if (_activeIntent == VisitIntent.reports) {}
final a=ExpressRoundScreen(company: c);
final b=NewInspectionScreen(
  initialCompany: c,
  fieldMode: true
);
final c=SafetyObservationFormScreen(company: c, sectors: sectors);
final d=FieldOperationalControlScreen(initialCompanyId: c.id);
final e=HistoryScreen(companyId: c.id);
final f=ManagerReportsScreen(company: c);
final g=CompanyDetailScreen(company: c);
const Text('Registrar outra ocorrência nesta empresa?');
"""
with tempfile.TemporaryDirectory() as d:
    root=Path(d)
    target=root/"lib/screens/quick_visit_screen.dart"
    target.parent.mkdir(parents=True)
    target.write_text(fixture,encoding="utf-8")
    result=subprocess.run([sys.executable,str(regression),str(root)],
       capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    target.write_text(fixture.replace("CompanyDetailScreen(company: c)", "MissingScreen()"),
        encoding="utf-8")
    negative=subprocess.run([sys.executable,str(regression),str(root)],
       capture_output=True,text=True)
    assert negative.returncode!=0, "Checker accepted missing route"
print("NAVIGATION_REGRESSION_TEST_OK")
