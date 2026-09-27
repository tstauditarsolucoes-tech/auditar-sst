#!/usr/bin/env python3
"""Version metadata after validating multiple individual client logins per company."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
versions={'android':('3.29.134+276','3.29.135+277'),
          'windows':('3.30.54+241','3.30.55+242')}
if platform not in versions: raise SystemExit('Invalid platform')
old,new=versions[platform]
p=root/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
if s.count('version: '+old)!=1:
    raise SystemExit('Unexpected version; refusing change')
p.write_text(s.replace('version: '+old,'version: '+new,1),
             encoding='utf-8',newline='\n')
print('MULTI_CLIENT_ACCESS_VERSION_OK '+new)
