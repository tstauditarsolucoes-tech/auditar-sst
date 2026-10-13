#!/usr/bin/env python3
"""Anchor contract for compact and dart-formatted NR18 quick action."""
import re
p=re.compile(r"label\s*:\s*const\s+Text\s*\(\s*'Abrir Vistoria'\s*,?\s*\)\s*,?\s*\)\s*,")
samples=[
  "label:const Text('Abrir Vistoria')),",
  "label: const Text('Abrir Vistoria'),\n  ),",
]
for s in samples:assert len(p.findall(s))==1,s
assert not p.search("label: const Text('Ronda com fotos'),\n),")
print("NR18_ACTION_PLAN_ANCHOR_OK")
