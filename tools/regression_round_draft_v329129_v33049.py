#!/usr/bin/env python3
"""Regression guard: local-only Ronda drafts and existing photo recovery; no sync modifications."""
from pathlib import Path
import sys,re
root=Path(sys.argv[1])
screen=(root/'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
storage=(root/'lib/services/express_round_draft_storage.dart').read_text(encoding='utf-8')
test=(root/'test/express_round_draft_storage_test.dart').read_text(encoding='utf-8')
checks=[
 'ExpressRoundDraftStorage.load(', 'ExpressRoundDraftStorage.save(',
 'ExpressRoundDraftStorage.clear(', '_roundDraftEntryId',
 '_roundDraftPayload()', '_scheduleRoundDraft()', '_flushRoundDraft(',
 '_roundDraftTail', "localDraftEntryId", 'Rascunho salvo neste aparelho',
 'Rascunho restaurado neste aparelho', 'Há uma ocorrência no rascunho.',
 'Confirme o backup das fotos', 'photoAvailable ? path', 'photoPath = persisted',
 'MediaSyncService.restoreRoundMedia(', 'Verificar e recuperar fotos salvas',
 'WidgetsBindingObserver', 'AppLifecycleState.paused',
 'File(persisted).length()', 'roundRecords.add(record)',
]
for token in checks:
 if token not in screen:raise SystemExit('ROUND_DRAFT missing: '+token)
assert re.search(r'await\s+AppDatabase\.instance\.upsertSstRecord\(record\)',screen)
assert re.search(r'await\s+ExpressRoundDraftStorage\.clear\(',screen)
assert re.search(r'if\s*\(_roundDraftHasContent\s*&&\s*!viewingHistoricalRound\)',screen)
assert screen.count('Future<void> _flushRoundDraft(')==1
assert "registerRoundPhoto(" in screen and "sendPendingMediaNow()" in screen
for token in ['auditar_round_drafts','draftSchema',".bak","target.rename(backup.path)","temp.rename(target.path)","file.readAsString()"]:
 if token not in storage:raise SystemExit('DRAFT_STORAGE missing: '+token)
assert 'root: temp' in test
assert 'corrupt primary can recover' in test
print('ROUND_DRAFT_RECOVERY_REGRESSION_OK')
