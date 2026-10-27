#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
p = root / 'lib/screens/express_round_screen.dart'
s = p.read_text(encoding='utf-8')
old = """                    const Expanded(
                      child: Text(
                        viewingHistoricalRound
"""
new = """                    Expanded(
                      child: Text(
                        viewingHistoricalRound
"""
if new not in s:
    if old not in s:
        raise RuntimeError('Marcador ausente: titulo dinamico do historico')
    s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8', newline='\n')
assert new in s
print('Compile fix v3.29.61 aplicado: titulo historico deixa de ser const dinamico.')
