#!/usr/bin/env python3
from pathlib import Path
import sys,re

root=Path(sys.argv[1])
version=sys.argv[2] if len(sys.argv)>2 else ""

ai=(root/"lib/services/ai_assistant_service.dart").read_text(encoding="utf-8")
q=(root/"lib/services/inspection_photo_ai_queue_service.dart").read_text(encoding="utf-8")
c=(root/"lib/screens/checklist_screen.dart").read_text(encoding="utf-8")
pub=(root/"pubspec.yaml").read_text(encoding="utf-8")

start=ai.find("  static Future<AiAssistantReply> analyzeChecklistPhotos({")
end=ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({",start)
assert start>=0 and end>start
method=ai[start:end]
assert "_prepareRoundPhotoForAi(originalBytes)" in method
assert "'rondaDeferred': true" in method
assert "_prepareImage(originalBytes)" not in method
assert "photoPaths.take(4)" in method

r0=q.find("  static Future<AiAssistantReply> _analyzeWithRetry({")
r1=q.find("  static String _photoFingerprint",r0)
assert r0>=0 and r1>r0
retry=q[r0:r1]
assert "for (var attempt" not in retry
assert retry.count("analyzeChecklistPhotos(")==1

assert "eligibleForLaterAi && aiStatus.isEmpty" in c
bad="""!const ['PRONTA_REVISAO', 'APLICADA', 'DESCARTADA']
            .contains(aiStatus)"""
assert bad not in c
assert "instabilidade da Central" not in c
assert "As fotos continuam salvas" in c
assert "InspectionPhotoAiQueueService.setSuggestionListener" in c
assert "Usar e editar" in c
assert "observations[questionId]!.text = description" in c
assert "risks[questionId]!.text = risk" in c
assert "recommendations[questionId]!.text = recommendation" in c

# O transporte geral continua com opt-in: nada libera timeout longo para sync.
http=(root/"lib/services/apps_script_http.dart").read_text(encoding="utf-8")
assert "bool allowLongAndroidRequest = false" in http
assert "androidDirect && !allowLongAndroidRequest" in http
assert "const Duration(seconds: 10)" in http

if version:
    assert f"version: {version}" in pub

print("CHECKLIST_AI_STABLE_REGRESSION_OK",version)
