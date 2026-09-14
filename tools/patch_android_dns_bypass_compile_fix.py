#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
path = root / 'lib/services/apps_script_http.dart'
text = path.read_text(encoding='utf-8')
old = """    final io = HttpClient()\n      ..findProxy = (_) => 'DIRECT'\n      ..connectionFactory = (uri, proxyHost, proxyPort) async {\n"""
new = """    final io = HttpClient();\n    io.findProxy = (_) => 'DIRECT';\n    io.connectionFactory = (uri, proxyHost, proxyPort) async {\n"""
if old not in text:
    raise RuntimeError('Bloco HttpClient DNS fallback não localizado')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8', newline='\n')
print('Compile fix DNS fallback aplicado.')
