#!/usr/bin/env python3
"""Safeguard worksite diary history and the original cloud payload."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
s=(root/'lib/screens/worksite_followup_screen.dart').read_text(encoding='utf-8')
test=(root/'test/worksite_diary_archive_test.dart').read_text(encoding='utf-8')
assert s.count('class WorksiteDiaryArchive')==1
for value in ['await WorksiteDiaryArchive.preserve','WorksiteDiaryArchive.overflow(value)',
 'WorksiteDiaryArchive.recent(value)','WorksiteFollowupCloudService.publish',
 'WorksiteFollowupCloudService.read','Ver registros anteriores']:
 assert value in s,value
add=s.split('Future<void> _addLog()',1)[1].split('WorksiteFollowup _currentForm()',1)[0]
assert not re.search(r'\[\s*result\s*,\s*\.\.\._record\.log\s*\]\s*\.take\s*\(\s*80\s*\)',add)
assert 'class WorksiteFollowup' in s and "'log':log.take(80)" in re.sub(r'\s+','',s)
assert "81 registros conservam 80 atuais" in test
print('WORKSITE_DIARY_ARCHIVE_REGRESSION_OK')
