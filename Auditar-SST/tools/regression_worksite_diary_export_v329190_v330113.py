#!/usr/bin/env python3
"""Pure guard: full diary export is opt-in and does not touch original SST core."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
screen=(root/'lib/screens/worksite_followup_screen.dart').read_text(encoding='utf-8')
assert screen.count('class WorksiteDiaryArchive')==1
assert 'static String exportText(' in screen
assert 'WorksiteDiaryArchive.unique(current,archived)' in screen
assert 'WorksiteDiaryArchive.unique(_record.log,older).length.toString()' in screen
assert 'Future<void> _copyCompleteDiary()' in screen
assert 'Clipboard.setData(ClipboardData(text:full))' in screen.replace(' ','').replace('\n','') or 'Clipboard.setData(ClipboardData(text: full))' in screen
assert "Copiar diário completo" in screen
assert 'WorksiteDiaryArchive.load(widget.company.id,user)' in screen.replace('\n','')
assert 'AuthService.canAccessCompany(widget.company.id)' in screen
assert 'WorksiteFollowupCloudService.publish' in screen
assert 'Ver registros anteriores' in screen
assert 'NR-18' in screen
assert 'WorksiteFollowupStore.save' in screen
print('FULL_WORKSITE_DIARY_EXPORT_REGRESSION_OK')
