#!/usr/bin/env python3
from pathlib import Path
import sys
path=Path(sys.argv[1])/'pubspec.yaml'
source=path.read_text(encoding='utf-8')
old='version: 3.29.126+268'
new='version: 3.29.127+269'
if source.count(old)!=1: raise SystemExit('Unexpected version: no file changed')
path.write_text(source.replace(old,new,1),encoding='utf-8',newline='\n')
print('PAPER_AI_VERSION_OK: 3.29.127+269')
