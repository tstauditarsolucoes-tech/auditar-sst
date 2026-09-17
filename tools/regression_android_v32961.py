#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('app/Auditar_SST_v1_5_dashboard')
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
coord=(root/'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
dev=(root/'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
http=(root/'lib/services/apps_script_http.dart').read_text(encoding='utf-8')
ai=(root/'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
ronda=(root/'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
assert 'version: 3.29.61+203' in pub
assert 'Duration(seconds: 2)' in coord and 'Duration(seconds: 5)' in coord
assert dev.count("'limit': 500,") >= 2
assert 'androidDirect && !allowLongAndroidRequest' in http
assert "'rondaDeferred': true" in ai
assert "final rondaDeferred = payload['rondaDeferred'] == true;" in ai
assert 'const Duration(seconds: 95)' in ai
assert 'const Duration(seconds: 55)' in ai
assert re.search(r'allowLongAndroidRequest\s*:\s*true', ai)
assert "'mode': 'checklist_photo'" in ai
assert '_prepareRoundPhotoForAi' in ai and 'maxDimension = 720' in ai and 'quality: 55' in ai
assert '_showRoundsArchive' in ronda and 'Histórico de Rondas Expressas' in ronda
assert '_loadRoundById' in ronda and 'viewingHistoricalRound' in ronda
assert '_historicalRoundBody' in ronda and '_historicalBottomBar' in ronda
assert 'Voltar à ronda atual' in ronda
assert '_reviewDeferredAiSuggestion' in ronda
assert 'A IA não altera o registro automaticamente' in ronda
assert 'Aprovar e salvar' in ronda and 'Manter pendente' in ronda
assert "..['aiReviewedByTechnician'] = true" in ronda
assert "..['aiStatus'] = 'CONCLUIDA'" in ronda
assert re.search(
    r'final\s+approved\s*=\s*await\s+_reviewDeferredAiSuggestion\(\s*record\s*,\s*reply\.result\s*,?\s*\);',
    ronda,
    re.S,
)
# Garante que a análise em lote não grava resultado da IA antes da confirmação do técnico.
batch = ronda.split('Future<void> _analyzePendingRoundPhotos() async {',1)[1].split('Future<void> _showRoundHistory() async {',1)[0]
assert batch.index('_reviewDeferredAiSuggestion') < batch.index("..['aiAssisted'] = true")
assert 'await ManagementPanelService.syncCompany(widget.company)' not in ronda
print('REGRESSAO_OK: sync 2s/5s preservado; histórico pós-fechamento; IA só grava após revisão/aprovação do técnico')
