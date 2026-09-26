#!/usr/bin/env python3
"""Release version only, after Ronda regression checks."""
from pathlib import Path
import re, sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
file=root/'pubspec.yaml'
s=file.read_text(encoding='utf-8')
old,new=('3.29.117+259','3.29.118+260') if platform=='android' else ('3.30.41+228','3.30.42+229')
assert s.count('version: '+old)==1, [line for line in s.splitlines() if line.startswith('version:')]
s=s.replace('version: '+old,'version: '+new,1)
file.write_text(s,encoding='utf-8',newline='\n')
print('RONDA_RELEASE_VERSION_OK',new)
