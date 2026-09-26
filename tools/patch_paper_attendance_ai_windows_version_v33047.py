#!/usr/bin/env python3
"""Windows version bump after the existing paper-sheet UI patches."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
old='version: 3.30.46+233'
new='version: 3.30.47+234'
if s.count(old)!=1: raise SystemExit('Unexpected Windows version; no files changed')
p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')
print('PAPER_AI_WINDOWS_VERSION_OK: 3.30.47+234')
