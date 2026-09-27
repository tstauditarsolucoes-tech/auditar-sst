#!/usr/bin/env python3
"""Bump only app metadata after managerial reports patch passes."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
versions={'android':('3.29.133+275','3.29.134+276'),
          'windows':('3.30.53+240','3.30.54+241')}
if platform not in versions:raise SystemExit('Invalid platform')
old,new=versions[platform];p=root/'pubspec.yaml';s=p.read_text(encoding='utf-8')
if s.count('version: '+old)!=1:raise SystemExit('Unexpected version; refusing change')
p.write_text(s.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
print('MANAGER_REPORTS_VERSION_OK '+new)
