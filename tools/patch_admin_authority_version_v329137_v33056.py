#!/usr/bin/env python3
"""Bump only the application version after admin regressions and Flutter tests."""
from pathlib import Path
import sys

root=Path(sys.argv[1]); platform=sys.argv[2]
versions={
    'android':('3.29.135+277','3.29.136+278'),
    'windows':('3.30.55+242','3.30.56+243'),
}
if platform not in versions:
    raise SystemExit('Use android or windows')
old,new=versions[platform]
path=root/'pubspec.yaml'
source=path.read_text(encoding='utf-8')
if source.count('version: '+old)!=1:
    raise SystemExit('Unexpected app version; refusing update.')
path.write_text(source.replace('version: '+old,'version: '+new,1),
                encoding='utf-8',newline='\n')
print('ADMIN_AUTHORITY_VERSION_OK '+new)
