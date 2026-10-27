#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]);platform=sys.argv[2]
versions={'android':('3.29.131+273','3.29.132+274'),
          'windows':('3.30.51+238','3.30.52+239')}
if platform not in versions:raise SystemExit('Invalid platform')
old,new=versions[platform];p=root/'pubspec.yaml'
s=p.read_text(encoding='utf-8')
if s.count('version: '+old)!=1:raise SystemExit('Unexpected app version; refusing change')
p.write_text(s.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
print('COMPANY_CLIENT_ACCESS_VERSION_OK '+new)
