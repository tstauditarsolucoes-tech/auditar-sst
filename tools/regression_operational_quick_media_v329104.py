#!/usr/bin/env python3
"""Regression for isolated rapid checklist capture, evidence queue, and clear sync status."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
expected=sys.argv[2]
sync=(root/'lib/services/device_sync_service.dart').read_text(encoding='utf8')
home=(root/'lib/screens/home_screen.dart').read_text(encoding='utf8')
check=(root/'lib/screens/checklist_screen.dart').read_text(encoding='utf8')
media=(root/'lib/services/media_sync_service.dart').read_text(encoding='utf8')
ai=(root/'lib/services/ai_assistant_service.dart').read_text(encoding='utf8')
pub=(root/'pubspec.yaml').read_text(encoding='utf8')
assert "Duration(seconds: 15)" in sync and "_activeMediaSync == null" in sync
assert "uploadPending(limit: 2)" in sync
assert "uploadPending(limit: 1).timeout" not in sync
assert "if (sent == 0 && received == 0)" not in sync
assert 'Future<int> pendingChangesCount()' in sync
assert 'Future<int> pendingCount()' in media
assert 'Future<void> _captureQuickNonConformities()' in check
assert "Salvar e próxima ocorrência" in check
assert "Salvar e melhorar texto com IA (opcional)" in check
assert 'InspectionPhotoAiQueueService.rememberMeta(' in check
assert "MANUAL_ONLY" in check
assert "await _saveDraft();" in check
assert "await _improveTextWithAi(item)" in check
assert "Fotos/assinaturas pendentes" in home
assert "Cadastros pendentes" in home
assert 'MediaSyncService.pendingCount()' in home
assert "'images':" not in ai[ai.index('static Future<AiAssistantReply> improveInspectionText('):ai.index('static Future<AiAssistantReply> analyzeChecklistPhotos(')]
assert f'version: {expected}' in pub
print('OPERATIONAL_QUICK_MEDIA_REGRESSION_OK',expected)
