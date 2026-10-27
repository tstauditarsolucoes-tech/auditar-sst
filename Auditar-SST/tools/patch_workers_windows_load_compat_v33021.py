#!/usr/bin/env python3
"""Adapta apenas a chamada de _load() na tela Windows de trabalhadores."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"lib/screens/workers_screen.dart"
text=p.read_text(encoding="utf-8")
old="await _load(showLoading: false);"
if text.count(old)!=1:
    raise RuntimeError("Chamada de recarregamento Windows não localizada")
text=text.replace(old,"await _load();",1)
p.write_text(text,encoding="utf-8",newline="\n")
print("WORKERS_WINDOWS_LOAD_COMPAT_OK")
