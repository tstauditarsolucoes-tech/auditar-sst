#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')
ronda = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
ai = (root / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
coord = (root / 'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
dev = (root / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
media = (root / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
companies = (root / 'lib/screens/companies_screen.dart').read_text(encoding='utf-8')
dds = (root / 'lib/screens/sst_records_screen.dart').read_text(encoding='utf-8')

assert 'version: 3.30.4+191' in pub

# Ronda Expressa no mesmo nível funcional do Android v3.29.61.
assert '_showRoundsArchive' in ronda
assert 'Histórico de Rondas Expressas' in ronda
assert '_loadRoundById' in ronda and 'viewingHistoricalRound' in ronda
assert '_historicalRoundBody' in ronda and '_historicalBottomBar' in ronda
assert 'Voltar à ronda atual' in ronda
assert '_reviewDeferredAiSuggestion' in ronda
assert 'A IA não altera o registro automaticamente' in ronda
assert 'Aprovar e salvar' in ronda and 'Manter pendente' in ronda
assert "..['aiReviewedByTechnician'] = true" in ronda
assert "..['aiStatus'] = 'CONCLUIDA'" in ronda
batch = ronda.split('Future<void> _analyzePendingRoundPhotos() async {', 1)[1].split('Future<void> _showRoundHistory() async {', 1)[0]
assert batch.index('_reviewDeferredAiSuggestion') < batch.index("..['aiAssisted'] = true")

# Foto IA normalizada + fallback isolado da Ronda publicada no GS.
assert "'mode': 'checklist_photo'" in ai
assert "'rondaDeferred': true" in ai
assert "final rondaDeferred = payload['rondaDeferred'] == true;" in ai
assert '_prepareRoundPhotoForAi' in ai
assert 'maxDimension = 720' in ai and 'quality: 55' in ai
assert 'const Duration(seconds: 95)' in ai and 'const Duration(seconds: 55)' in ai

# Windows mantém exatamente a estratégia própria de sincronização. A chamada
# ManagementPanelService da Ronda já existia no PC e é preservada de propósito.
assert 'Duration(seconds: 10)' in coord
assert 'final pullLimit = isWindows ? 500 : 100;' in dev
assert 'pullWhenClean: true' in coord
assert 'force: force' in coord
assert 'ManagementPanelService.syncCompany(widget.company)' in ronda

# Regressões de funções já existentes no PC v3.30.3.
assert 'restoreCompanyLogos' in media
assert "'action': 'media_lookup'" in media
assert 'MediaSyncService.restoreCompanyLogos' in companies
assert 'MediaSyncService.uploadCompanyLogoNow' in companies
assert "'companies': {'logo_path'}" in dev
assert 'Retirar ficha do DDS' in dds

icon = root / 'windows/runner/resources/app_icon.ico'
assert icon.exists() and icon.stat().st_size > 10000

print('REGRESSAO_OK: Windows sync 10s/500 e sync gerencial preservados; logos/DDS preservados; Ronda pós-fechamento + revisão IA ativos.')
