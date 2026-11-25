#!/usr/bin/env python3
"""Verificacao estatica do modulo experimental de IA, sem foto ou dado real."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
panel = (root / 'feature_sources/sst_accident_photo_ai_v1.dart').read_text(encoding='utf-8')
screen = (root / 'feature_sources/sst_report_center_screen_v1.dart').read_text(encoding='utf-8')
patch = (root / 'tools/patch_sst_report_center_v1.py').read_text(encoding='utf-8')
tests = (root / 'feature_sources/sst_accident_photo_ai_test_v1.dart').read_text(encoding='utf-8')

assert panel.count('class SstAccidentPhotoAiPanel') == 1
assert panel.count('AiAssistantService.analyzeSafetyObservationPhoto(') == 1
assert panel.count('showDialog<bool>(') == 1, 'Confirmacao explicita de envio'
assert 'Confirmar envio' in panel
assert 'accepted != true' in panel
assert 'privacyAccepted' in panel
assert 'Fotos' not in panel or 'foto' in panel.lower()
assert 'dados pessoais' in panel
assert 'o serviço de IA já utilizado' in panel
assert 'AuthService.canAccessCompany(widget.company.id)' in panel
assert 'AppDatabase.activeUserId.toString()' in panel
assert 'companyId != widget.company.id' in panel
assert 'photoPaths' in panel and 'take(2)' in panel
assert 'A fotografia nao comprova' in panel
assert 'NAO EXECUTADA' in panel and 'NAO CONFIRMADO' in panel
assert "observationKind: 'Acidente/incidente'" in panel
assert 'onReviewSuggestion(questionId, suggestionText)' in panel
assert 'http.post(' not in panel and 'Uri.parse(' not in panel
assert 'upsert' not in panel and 'setSetting(' not in panel
assert "import 'sst_accident_photo_ai.dart';" in screen
assert 'SstAccidentPhotoAiPanel(' in screen
assert "_reviewVisualAiSuggestion(" in screen
assert "SstFieldStatus.notChecked" in screen
assert "if(isIncident)" in screen and "SstAccidentInvestigationGuide(" in screen
assert 'SstFieldDraftStore.save(' in screen
assert 'sst_accident_photo_ai_v1.dart' in patch
assert 'sst_accident_photo_ai_test_v1.dart' in patch
assert 'SstAccidentPhotoAiSuggestion.fromResult(' in tests
assert tests.count("test('") >= 4
print('ACCIDENT_PHOTO_AI_PREFLIGHT_OK: opt-in, privacy, isolation, review')
