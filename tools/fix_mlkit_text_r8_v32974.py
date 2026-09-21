#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
rules = root / 'android' / 'app' / 'proguard-rules.pro'
rules.parent.mkdir(parents=True, exist_ok=True)

existing = rules.read_text(encoding='utf-8') if rules.exists() else ''
required = [
    '-dontwarn com.google.mlkit.vision.text.chinese.**',
    '-dontwarn com.google.mlkit.vision.text.devanagari.**',
    '-dontwarn com.google.mlkit.vision.text.japanese.**',
    '-dontwarn com.google.mlkit.vision.text.korean.**',
]

lines = existing.splitlines()
changed = False
for rule in required:
    if rule not in lines:
        lines.append(rule)
        changed = True

text = '\n'.join(lines).rstrip() + '\n'
rules.write_text(text, encoding='utf-8')

for rule in required:
    if rule not in text:
        raise SystemExit('Regra R8 ausente: ' + rule)

print('MLKIT_R8_OK: idiomas opcionais ignorados; OCR latino permanece ativo.')
