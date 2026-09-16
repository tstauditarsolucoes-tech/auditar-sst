#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
aip = root / 'lib/services/ai_assistant_service.dart'
ai = aip.read_text(encoding='utf-8')


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

# Marca exclusivamente a analise de foto iniciada pela Ronda Expressa. O GS
# ignora este campo; ele e usado apenas pelo transporte do app para escolher um
# tempo maior sem tocar na sincronizacao nem no Checklist comum.
ai = once(
    ai,
    """      final reply = await _send({\n        'mode': 'checklist_photo',\n        'companyName': company.name,\n""",
    """      final reply = await _send({\n        'mode': 'checklist_photo',\n        'rondaDeferred': true,\n        'companyName': company.name,\n""",
    'marcador rondaDeferred',
)

# O Checklist permanece com 55 s. Somente a Ronda pos-campo recebe 95 s, pois
# ela nao esta mais no caminho critico da vistoria e o Gemini pode oscilar.
ai = once(
    ai,
    """    final aiMode = '${payload['mode'] ?? ''}';\n    final requestTimeout =\n        aiMode == 'checklist_photo' || aiMode == 'safety_observation_photo'\n            ? const Duration(seconds: 55)\n            : aiMode == 'report_review_chat'\n                ? const Duration(seconds: 75)\n                : const Duration(seconds: 65);\n""",
    """    final aiMode = '${payload['mode'] ?? ''}';\n    final rondaDeferred = payload['rondaDeferred'] == true;\n    final requestTimeout = rondaDeferred\n        ? const Duration(seconds: 95)\n        : aiMode == 'checklist_photo' || aiMode == 'safety_observation_photo'\n            ? const Duration(seconds: 55)\n            : aiMode == 'report_review_chat'\n                ? const Duration(seconds: 75)\n                : const Duration(seconds: 65);\n""",
    'timeout seletivo da IA',
)

aip.write_text(ai, encoding='utf-8', newline='\n')

assert "'rondaDeferred': true" in ai
assert "final rondaDeferred = payload['rondaDeferred'] == true;" in ai
assert 'const Duration(seconds: 95)' in ai
assert 'const Duration(seconds: 55)' in ai
assert 'allowLongAndroidRequest: true' in ai
print('v3.29.60: IA pos-ronda com 95 s; Checklist 55 s e sincronizacao rapida preservados.')