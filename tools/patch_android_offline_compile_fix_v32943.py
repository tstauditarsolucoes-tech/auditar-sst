#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
authp = root / 'lib/services/auth_service.dart'
text = authp.read_text(encoding='utf-8')
old = "    var bytes = utf8.encode('$salt|${_normalizeOfflineLogin(identifier)}|$password');\n"
new = "    List<int> bytes = utf8.encode('$salt|${_normalizeOfflineLogin(identifier)}|$password');\n"
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise RuntimeError('Bloco do verificador offline não localizado')
authp.write_text(text, encoding='utf-8', newline='\n')
print('Compile fix do modo offline Android aplicado.')
