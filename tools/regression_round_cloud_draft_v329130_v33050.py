#!/usr/bin/env python3
"""Cloud drafts use existing SST/media sync, never modify its implementation."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
ui=(root/'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
cloud=(root/'lib/services/express_round_cloud_draft_service.dart').read_text(encoding='utf-8')
for token in (
  'ExpressRoundCloudDraftService.publish(',
  'ExpressRoundCloudDraftService.restore(',
  'ExpressRoundCloudDraftService.list(',
  'ExpressRoundCloudDraftService.complete(',
  'ExpressRoundDraftStorage.save(',
  'Continuar rascunho da nuvem',
  'Na nuvem • texto e fotos com backup confirmado',
  'Backup pendente • cópia preservada neste aparelho',
  "'cloudPhotoRefs': Map<String, dynamic>.from(_cloudPhotoRefs)",
):
 if token not in ui: raise SystemExit('CLOUD_DRAFT_UI missing '+token)
for token in (
  "draftType = 'RONDA_RASCUNHO'",
  "photoType = 'round_draft_photo'",
  "'photoPath'] = ''",
  "'photoPath2'] = ''",
  "sha256.convert(bytes)",
  "await DeviceSyncService.pendingChangesCount()",
  "await DeviceSyncService.synchronize(force: true)",
  "await MediaSyncService.uploadPending(limit: 12)",
  "['drive_file_id']",
  "'dirty'",
  "record.companyId != companyId",
  "record.status != 'RASCUNHO'",
  "MediaSyncService.trainingRecordMediaLocalPath(",
  "status: 'CONCLUIDO'",
):
 if token not in cloud: raise SystemExit('CLOUD_DRAFT_SERVICE missing '+token)
if 'await ExpressRoundCloudDraftService.complete(' not in ui:
 raise SystemExit('Missing cloud completion marker')
assert ui.count('Future<void> _publishCloudRoundDraft(')==1
assert ui.count('Future<void> _openCloudRoundDrafts(')==1
assert cloud.count('static Future<bool> publish(')==1
print('CLOUD_DRAFT_EXISTING_SYNC_AND_MEDIA_REGRESSION_OK')
