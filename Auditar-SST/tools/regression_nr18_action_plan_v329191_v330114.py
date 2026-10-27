#!/usr/bin/env python3
"""Regression contract for the NR18 context action: no automatic NC mutation."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])
s=(root/"lib/screens/nr18_field_checklist_screen.dart").read_text(encoding="utf-8")
assert s.count("import 'action_plan_screen.dart';")==1
assert s.count("ActionPlanScreen(companyId:widget.company.id)")==1
assert s.count("Plano de ação da obra")==1
assert s.count("Ronda com fotos")==1 and s.count("Abrir Vistoria")==1
assert "onPressed:authorized?()=>_open(" in s
assert "AuthService.canAccessCompany(widget.company.id)" in s
assert "Nr18FieldDraftStore" in s
assert "WorksiteFollowupCloudService" not in s
print("NR18_ACTION_PLAN_NAVIGATION_REGRESSION_OK")
