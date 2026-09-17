#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
path = root / 'lib/services/web_service_config.dart'
text = path.read_text(encoding='utf-8')

OLD_AUDITAR_ENDPOINT = (
    'https://script.google.com/macros/s/'
    'AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec'
)

text = text.replace('AUDITAR_APPS_SCRIPT_URL', 'SST_APPS_SCRIPT_URL')
text = text.replace('AUDITAR_SYNC_KEY', 'SST_SYNC_KEY')

# A edição neutra nunca pode cair silenciosamente na Central original.
# O endpoint passa a ser obrigatório no build por SST_APPS_SCRIPT_URL.
text = text.replace(OLD_AUDITAR_ENDPOINT, '')

# Também cobre qualquer defaultValue de endpoint herdado que não tenha sido
# exatamente o deployment conhecido acima.
text = re.sub(
    r"(static const String endpoint = String\.fromEnvironment\(\s*"
    r"'SST_APPS_SCRIPT_URL',\s*defaultValue:\s*)'https://script\.google\.com/macros/s/[^']+/exec'",
    r"\1''",
    text,
    flags=re.S,
)

path.write_text(text, encoding='utf-8', newline='\n')

assert 'SST_APPS_SCRIPT_URL' in text
assert 'SST_SYNC_KEY' in text
assert 'AUDITAR_APPS_SCRIPT_URL' not in text
assert 'AUDITAR_SYNC_KEY' not in text
assert OLD_AUDITAR_ENDPOINT not in text
assert "defaultValue:\n        ''" in text or "defaultValue: ''" in text

print(
    'Configuração neutra isolada: URL e chave SST_* obrigatórias; '
    'nenhum fallback para a Central original.'
)
