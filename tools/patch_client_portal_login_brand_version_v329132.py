#!/usr/bin/env python3
"""Version metadata only; the portal HTML is the only functional change."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
platform=sys.argv[2]
versions={'android':('3.29.130+272','3.29.131+273'),
          'windows':('3.30.50+237','3.30.51+238')}
if platform not in versions:raise SystemExit('Use android or windows')
old,new=versions[platform]
p=root/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
if s.count('version: '+old)!=1:raise SystemExit('Unexpected base version; no change')
p.write_text(s.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
print('AUDITAR_BRANDED_PORTAL_VERSION_OK '+new)
