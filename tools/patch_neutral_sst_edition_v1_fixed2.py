#!/usr/bin/env python3
from pathlib import Path

source_path = Path(__file__).with_name('patch_neutral_sst_edition_v1_fixed.py')
source = source_path.read_text(encoding='utf-8')
old = "def replace_in(path: Path, replacements):\n    rel ="
new = "def replace_in(path: Path, replacements):\n    if not path.exists():\n        return\n    rel ="
if old not in source:
    raise SystemExit('Ponto de compatibilidade replace_in não encontrado')
source = source.replace(old, new, 1)
exec(compile(source, str(source_path), 'exec'), {'__name__': '__main__', '__file__': str(source_path)})
