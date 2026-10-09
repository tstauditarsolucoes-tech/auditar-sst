#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
widget = (root / 'lib/widgets/offline_report_inline_suggestions.dart').read_text(encoding='utf-8')
screen = (root / 'lib/screens/safety_observations_screen.dart').read_text(encoding='utf-8')
service = (root / 'lib/services/offline_report_knowledge_service.dart').read_text(encoding='utf-8')
pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')

for snippet in (
    "Sugestões do histórico",
    "Funciona sem internet",
    "offline_report_knowledge_v1.json",
    "auditar-extintor-sem-sinalizacao",
    "auditar-sensor-protecao-inoperante",
    "auditar-painel-eletrico-aberto",
    "decodeAndRankForTesting",
):
    assert snippet in widget, 'sugestao inline incompleta: ' + snippet

for snippet in (
    "OfflineReportInlineSuggestions(",
    "valueListenable: title",
    "title.text = selected.title",
    "fillEmpty(description, selected.description)",
    "fillEmpty(risk, selected.risk)",
    "fillEmpty(recommendation, selected.recommendation)",
    "OfflineReportKnowledgeService.markUsed(selected.id)",
):
    assert snippet in screen, 'integracao no primeiro campo ausente: ' + snippet

assert "Usar modelo offline" in screen
assert "Guardar como modelo" in screen
assert "learnFromApprovedFields" in service
assert "offline_report_knowledge_v1.json" in service

for forbidden in (
    "DeviceSyncService", "AppsScriptHttp", "MediaSyncService",
    "DriveService", "AiAssistantService", "../database.dart",
):
    assert forbidden not in widget, 'dependencia proibida na sugestao inline: ' + forbidden

assert (
    'version: 3.29.157+299' in pub
    or 'version: 3.30.76+263' in pub
), 'versao de sugestoes offline incorreta'

print('OFFLINE_INLINE_SUGGESTIONS_REGRESSION_OK')
print('FIRST_FIELD_TITLE_AUTOSUGGEST_OK')
print('LOCAL_LEARNED_KNOWLEDGE_REUSED_OK')
print('EXISTING_OFFLINE_LIBRARY_PRESERVED_OK')
print('NO_SYNC_DB_MEDIA_AI_OR_GS_DEPENDENCY_OK')
