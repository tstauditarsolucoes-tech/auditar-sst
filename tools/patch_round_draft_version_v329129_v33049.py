#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
v={'android':('3.29.128+270','3.29.129+271'),
   'windows':('3.30.48+235','3.30.49+236')}
if platform not in v:raise SystemExit('Specify android or windows')
old,new=v[platform];p=root/'pubspec.yaml';s=p.read_text(encoding='utf-8')
if s.count('version: '+old)!=1:raise SystemExit('Unexpected version; no file changed')
p.write_text(s.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
print('ROUND_DRAFT_VERSION_OK: '+new)
