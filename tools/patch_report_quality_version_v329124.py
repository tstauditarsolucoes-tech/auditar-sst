#!/usr/bin/env python3
"""Version bump for report quality v3.29.124; keeps permanent signing unchanged."""
from pathlib import Path
import sys
path=Path(sys.argv[1])/'pubspec.yaml'
source=path.read_text(encoding='utf-8')
old='version: 3.29.123+265'
new='version: 3.29.124+266'
if source.count(old)!=1: raise SystemExit('Unexpected version; no file changed')
path.write_text(source.replace(old,new,1),encoding='utf-8',newline='\n')
print('REPORT_QUALITY_VERSION_OK: 3.29.124+266')
