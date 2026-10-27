#!/usr/bin/env python3
"""Version bump for quality-only v3.29.125; permanent signer unchanged."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
old='version: 3.29.124+266'
new='version: 3.29.125+267'
if s.count(old)!=1: raise SystemExit('Unexpected version, no change')
p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')
print('REPORT_QUALITY_VERSION_OK: 3.29.125+267')
