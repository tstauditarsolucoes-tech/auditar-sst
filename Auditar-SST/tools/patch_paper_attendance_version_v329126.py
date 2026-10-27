#!/usr/bin/env python3
"""Bump version only, preserving the permanent signing configuration."""
from pathlib import Path
import sys
path=Path(sys.argv[1])/'pubspec.yaml'
old='version: 3.29.125+267'
new='version: 3.29.126+268'
s=path.read_text(encoding='utf-8')
if s.count(old)!=1:raise SystemExit('Unexpected version; no change made')
path.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')
print('PAPER_ATTENDANCE_VERSION_OK: 3.29.126+268')
