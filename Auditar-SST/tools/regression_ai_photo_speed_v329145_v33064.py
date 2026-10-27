#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
ai = (root / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
ronda = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')

for snippet in (
    "import 'dart:isolate';",
    "_preparePhotoForAiAsync",
    "maxDimension: single ? 720",
    "maxDimension: single ? 720 : (index == 0 ? 640 : 560)",
    "'rondaDeferred': false",
    "'rondaDeferred': true",
    "const Duration(seconds: 50)",
    "const Duration(seconds: 90)",
    "aiElapsedMs",
):
    assert snippet in ai, 'AI speed regression missing: ' + snippet

for snippet in (
    'Timer? _aiPhotoTimer;',
    '_aiPhotoElapsedSeconds',
):
    assert snippet in ronda, 'Ronda UX regression missing: ' + snippet

assert (
    'IA analisando foto • ${_aiPhotoElapsedSeconds}s' in ronda
    or 'Preparando foto para análise...' in ronda
), 'Ronda UX feedback de análise ausente'

print('AI_PHOTO_SPEED_REGRESSION_OK')
