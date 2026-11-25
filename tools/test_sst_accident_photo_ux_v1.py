#!/usr/bin/env python3
"""Preflight do refinamento fotográfico. Sem rede, fotos pessoais ou banco."""
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
panel = (repo / "feature_sources/sst_accident_photo_ai_v1.dart").read_text(encoding="utf-8")
screen = (repo / "feature_sources/sst_report_center_screen_v1.dart").read_text(encoding="utf-8")
tests = (repo / "feature_sources/sst_accident_photo_ai_test_v1.dart").read_text(encoding="utf-8")
patch = (repo / "tools/patch_sst_report_center_v1.py").read_text(encoding="utf-8")

assert "final Set<String> _selectedPaths" in panel
assert "_selectedPaths.contains(p)" in panel, "Sem seleção prévia automática"
assert "_selectedPaths.length >= 2" in panel, "Máximo 2 fotos"
assert "Selecione no máximo duas fotos" in panel
assert "privacyAccepted = false" in panel
assert "generation++;" in panel
assert "_identity(selectedPhotos) != selectedSignature" in panel
assert "_selectedPaths.clear();" in panel, "Limpar seleção na mudança de empresa/fotos"
assert "evidencePhotoCount" in panel and "evidencePhotoCount:" in screen
assert "Seleção individual para envio" in panel
assert "Confirmar envio" in panel and "accepted != true" in panel
assert "AuthService.canAccessCompany(widget.company.id)" in panel
assert "AppDatabase.activeUserId.toString()" in panel
assert "AiAssistantService.analyzeSafetyObservationPhoto(" in panel
assert "verificationQuestions" in panel
assert "Roteiro orientativo escolhido por palavras" in panel
assert "não representa nova identificação automática" in panel
assert "RegExp(r'máquina|maquina" in panel
assert "RegExp(r'escada|andaime" in panel
assert "RegExp(r'piso|água" in panel
assert "if (before.status != SstFieldStatus.notChecked)" in screen, (
    "Não sobrescrever item apurado")
assert "_attachAccidentPhoto(ImageSource source)" in screen
assert "for (final id in const ['incident-03', 'incident-04'])" in screen
assert "photoPaths.length < 2" in screen
assert "sst_accident_photo_ai_v1.dart" in patch
assert tests.count("test('") >= 7
assert "http.post(" not in panel and "setSetting(" not in panel
assert "upsert" not in panel and "delete(" not in panel
print("ACCIDENT_PHOTO_UX_PREFLIGHT_OK: explicit photo choice, review, provenance")
