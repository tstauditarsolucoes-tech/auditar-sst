#!/usr/bin/env python3
"""Apply isolated Ronda UI source patch from checked-in compressed bundle."""
import base64, gzip, runpy, sys, tempfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
payload = (root / 'build_sources/v3.29.118-ronda-reports/patch_ronda_ui_v329118.py.gz.b64').read_text(encoding='utf-8').strip()
script = gzip.decompress(base64.b64decode(payload)).decode('utf-8')
with tempfile.TemporaryDirectory(prefix='auditar_ronda_patch_') as tmp:
    target=Path(tmp)/'ronda_ui.py'
    target.write_text(script,encoding='utf-8')
    original=sys.argv
    try:
        sys.argv=[str(target),*original[1:]]
        runpy.run_path(str(target),run_name='__main__')
    finally:sys.argv=original
print('AUDITAR_RONDA_UI_BUNDLE_APPLIED')
