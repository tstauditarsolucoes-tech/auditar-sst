#!/usr/bin/env python3
"""Regressão da recuperação de conexão da IA da Ronda v3.29.151/v3.30.70."""
from pathlib import Path
import sys

if len(sys.argv) < 2:
    raise SystemExit(
        "uso: regression_ronda_ai_connection_recovery_v329151_v33070.py <APP_DIR>"
    )

root = Path(sys.argv[1])
ai = (root / "lib/services/ai_assistant_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

a = ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({")
b = ai.find("  static Future<AiAssistantReply> reviewExpressRound(", a)
assert a >= 0 and b > a
method = ai[a:b]

assert method.count("'mode': 'checklist_photo'") == 2
assert "'rondaDeferred': false" in method
assert "'rondaDeferred': true" in method
assert "'mode': 'safety_observation_photo'" not in method
assert "fastReply" in method
assert "timedOut" in method
assert "_preparePhotoForAiAsync" in method
assert "aiElapsedMs" in method

# A IA normal da vistoria continua com o seu próprio fluxo robusto.
c = ai.find("  static Future<AiAssistantReply> analyzeChecklistPhotos({")
d = ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({", c)
assert c >= 0 and d > c
checklist = ai[c:d]
assert checklist.count("'mode': 'checklist_photo'") >= 1
assert "'rondaDeferred': false" in checklist
assert "'rondaDeferred': true" in checklist

assert (
    "version: 3.29.151+293" in pub
    or "version: 3.30.70+257" in pub
)

print("RONDA_AI_CONNECTION_RECOVERY_REGRESSION_OK")
print("CHECKLIST_AI_FLOW_PRESERVED_OK")
