#!/usr/bin/env python3
"""NR18 field feature smoke test in the assembled Flutter app."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
screen=(root/"lib/screens/worksite_followup_screen.dart").read_text(encoding="utf-8")
nr=(root/"lib/screens/nr18_field_checklist_screen.dart").read_text(encoding="utf-8")
test=(root/"test/nr18_field_checklist_test.dart").read_text(encoding="utf-8")
assert "Nr18FieldChecklistScreen(" in screen
assert "onPressed:()=>_open(Nr18FieldChecklistScreen" in screen
assert "Nr18FieldDraftStore.key" in test
for field in ["andaimes","escavacao","quedas","eletrica","areas","pgr","altura"]:
    assert "Nr18FieldTopic('"+field+"'" in nr
assert "Nr18FieldStatus.notChecked" in nr
assert "AppDatabase.instance.setSetting" in nr
assert "Clipboard.setData" in nr
assert "NewInspectionScreen(" in nr and "ExpressRoundScreen(" in nr
assert "worksite_followup_sync_v1" not in nr
print("NR18_FIELD_REGRESSION_OK")
