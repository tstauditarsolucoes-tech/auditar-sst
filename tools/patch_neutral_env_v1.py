#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
path = root / 'lib/services/web_service_config.dart'
text = path.read_text(encoding='utf-8')
text = text.replace('AUDITAR_APPS_SCRIPT_URL', 'SST_APPS_SCRIPT_URL')
text = text.replace('AUDITAR_SYNC_KEY', 'SST_SYNC_KEY')
path.write_text(text, encoding='utf-8', newline='\n')
assert 'SST_APPS_SCRIPT_URL' in text
assert 'SST_SYNC_KEY' in text
assert 'AUDITAR_APPS_SCRIPT_URL' not in text
assert 'AUDITAR_SYNC_KEY' not in text
print('Configuração da edição neutra usa apenas nomes SST_*; endpoint e lógica permanecem os mesmos.')
