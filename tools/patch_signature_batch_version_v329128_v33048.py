#!/usr/bin/env python3
"""Only adjusts build metadata after batch signing patch and tests."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
versions={'android':('3.29.127+269','3.29.128+270'),
          'windows':('3.30.47+234','3.30.48+235')}
if platform not in versions:raise SystemExit('android or windows required')
old,new=versions[platform];p=root/'pubspec.yaml';body=p.read_text(encoding='utf-8')
if body.count('version: '+old)!=1:raise SystemExit('Version mismatch: no files changed')
p.write_text(body.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
print('SIGNATURE_BATCH_VERSION_OK: '+new)
