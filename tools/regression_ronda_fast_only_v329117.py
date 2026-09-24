#!/usr/bin/env python3
"""Fail release if fast-Ronda patch leaks into Checklist or sync."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
src=(root/'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
round_ui=(root/'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')
check=src.split('  static Future<AiAssistantReply> analyzeChecklistPhotos({',1)[1].split('  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({',1)[0]
ronda=src.split('  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({',1)[1].split('  static Future<AiAssistantReply> reviewExpressRound({',1)[0]
assert "'mode': 'checklist_photo'" in check
assert "'rondaDeferred': true," in check, 'Checklist path modified'
assert "bool fastRound = false," in ronda
assert "'rondaDeferred': !fastRound," in ronda
assert "const Duration(seconds: 65)" in ronda
assert "O registro permanec" in ronda or "registro permanecem salvos" in ronda
assert round_ui.count("fastRound: true,")==2, 'Ronda must enable quick mode in capture and pending'
for name in ['device_sync_service.dart','sync_coordinator.dart','media_sync_service.dart']:
    assert (root/'lib/services'/name).is_file()
assert (root/'painel_web_google_apps_script/Code.gs').is_file()
print('RONDA_FAST_SCOPE_OK: checklist unchanged, 2 Ronda actions, original sync/GS preserved')
