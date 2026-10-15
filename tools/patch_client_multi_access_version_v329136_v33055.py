#!/usr/bin/env python3
"""Metadata only, after multiple-client regression passes."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);platform=sys.argv[2]
versions={'android':('3.29.134+276','3.29.135+277'),
          'windows':('3.30.54+241','3.30.55+242')}
if platform not in versions:raise SystemExit('Use android or windows')
old,new=versions[platform]
pubspec=root/'pubspec.yaml'
s=pubspec.read_text(encoding='utf-8')
if s.count('version: '+old)!=1:
    raise SystemExit('Unexpected base version; refusing to update.')
pubspec.write_text(s.replace('version: '+old,'version: '+new,1),
                   encoding='utf-8',newline='\n')
print('MULTI_CLIENT_VERSION_OK '+new)
