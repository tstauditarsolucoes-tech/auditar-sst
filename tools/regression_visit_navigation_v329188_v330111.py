#!/usr/bin/env python3
"""Regression: all old routes and sequential NC capture remain available."""
from pathlib import Path
import re
import sys
s=(Path(sys.argv[1])/"lib/screens/quick_visit_screen.dart").read_text(encoding="utf-8")
# Dart formatter may wrap constructor arguments across lines; normalize
# whitespace only for route-presence checks. Do not edit app source.
compact=re.sub(r",(?=\))","",re.sub(r"\s+","",s))
assert s.count("class VisitIntentTabs extends StatelessWidget")==1
assert "_activeIntent=widget.intent;" in s
assert "selected:_activeIntent" in s
assert "switch (_activeIntent)" in s, "Header must follow selected tab"
assert "switch (widget.intent)" not in s, "Stale header after task switch"
for task in ["visit","drafts","pending","reports"]:
  assert "if (_activeIntent == VisitIntent."+task+")" in s,task
for route in ["ExpressRoundScreen(company: c)",
  "NewInspectionScreen(initialCompany: c, fieldMode: true)",
  "SafetyObservationFormScreen(company: c, sectors: sectors)",
  "FieldOperationalControlScreen(initialCompanyId: c.id)",
  "HistoryScreen(companyId: c.id)","ManagerReportsScreen(company: c)",
  "CompanyDetailScreen(company: c)",
  ]:
  assert re.sub(r"\s+","",route) in compact,route
# Preserve a way to capture another NC, whichever safe, localized UI is
# present. The original close-form prompt and the new button are equivalent
# for navigation; neither should imply successful persistence.
assert ("Registraroutraocorrêncianestaempresa?" in compact or
        ("Outroregistro" in compact and "Formuláriofechado" in compact)), (
    "Sequential NC capture action lost"
)
print("NAVIGATION_COMPANY_CONTEXT_REGRESSION_OK")
