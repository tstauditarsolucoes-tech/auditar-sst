#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
old='version: 3.29.125+267'
new='version: 3.29.126+268'
if s.count(old)!=1:
    raise SystemExit('Unexpected version; no file changed')
p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')
print('PHYSICAL_ATTENDANCE_VERSION_OK: 3.29.126+268')
