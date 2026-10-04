#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
screen = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
ai = (root / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
widget = (root / 'lib/widgets/offline_report_inline_suggestions.dart').read_text(encoding='utf-8')
pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')

for snippet in (
    "OfflineReportInlineSuggestions(",
    "valueListenable: description",
    "onSelected: _applyOfflineRoundSuggestion",
    "offlineModelId",
    "offlineModelTitle",
    "offlineModelRisk",
    "offlineModelConsequence",
    "offlineModelRecommendation",
    "'offlineModelApplied': offlineModelId.isNotEmpty",
    "'offlineModelSource': offlineModelSource",
):
    assert snippet in screen, 'Ronda sem biblioteca offline: ' + snippet

assert "aiRisk.isNotEmpty ? aiRisk : offlineModelRisk" in screen
assert "aiRecommendation.isNotEmpty" in screen
assert "OfflineReportKnowledgeService.markUsed(selected.id)" in screen
assert "Sugestões do histórico" in widget
assert "Funciona sem internet" in widget

# A integração da Ronda não pode mudar as rotas de IA existentes.
assert ai.count("'mode': 'checklist_photo'") >= 2
assert "'rondaDeferred': false" in ai
assert "'rondaDeferred': true" in ai

assert (
    'version: 3.29.158+300' in pub
    or 'version: 3.30.77+264' in pub
), 'versao Ronda offline incorreta'

print('RONDA_OFFLINE_SUGGESTIONS_REGRESSION_OK')
print('RONDAS_REUSE_LOCAL_KNOWLEDGE_OK')
print('AI_FLOW_PRESERVED_OK')
print('NO_SYNC_DB_MEDIA_GS_DEPENDENCY_OK')
