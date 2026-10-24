#!/usr/bin/env python3
"""Version bump for the first Auditar Android release signed by the new permanent key."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
path=root/'pubspec.yaml'
text=path.read_text(encoding='utf-8')
before='version: 3.29.122+264'
after='version: 3.29.123+265'
if text.count(before)!=1:
    raise SystemExit('PERMANENT_SIGNER_VERSION: unexpected source version, no file changed')
path.write_text(text.replace(before,after,1), encoding='utf-8',newline='\n')
print('PERMANENT_SIGNER_VERSION_OK: 3.29.123+265')
