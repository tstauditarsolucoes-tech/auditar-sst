#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
test_root = root / 'test'
if not test_root.exists():
    print('Sem testes locais para adaptar.')
    raise SystemExit(0)

replacements = [
    ('auditar_sst_session_token_v1', 'sst_gestao_session_token_v1'),
    ('auditar_sst_auth.json', 'sst_gestao_auth.json'),
]
changed = []
for path in test_root.rglob('*.dart'):
    text = path.read_text(encoding='utf-8')
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding='utf-8', newline='\n')
        changed.append(str(path.relative_to(root)))

print('Testes adaptados somente às chaves/arquivo locais da edição neutra:', ', '.join(changed) or 'nenhum')
