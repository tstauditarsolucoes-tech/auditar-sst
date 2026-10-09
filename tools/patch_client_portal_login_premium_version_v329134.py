#!/usr/bin/env python3
"""Version metadata only after the visual-only portal patch."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
versions={'android':('3.29.132+274','3.29.133+275'),
          'windows':('3.30.52+239','3.30.53+240')}
if platform not in versions:raise SystemExit('Invalid platform')
old,new=versions[platform];p=root/'pubspec.yaml';s=p.read_text(encoding='utf-8')
if s.count('version: '+old)!=1:raise SystemExit('Unexpected version; refusing change')
p.write_text(s.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
print('AUDITAR_CLIENT_LOGIN_PREMIUM_VERSION_OK '+new)
