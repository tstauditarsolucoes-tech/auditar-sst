#!/usr/bin/env python3
"""Apply isolated Ronda UI source patch from checked-in compressed bundle."""
import base64, gzip, runpy, sys, tempfile
from pathlib import Path
root = Path(__file__).resolve().parents[1]
payload = (root / 'build_sources/v3.29.118-ronda-reports/patch_ronda_ui_v329118.py.gz.b64').read_text(encoding='utf-8').strip()
script = gzip.decompress(base64.b64decode(payload)).decode('utf-8')
# Android and Windows have equivalent Ronda AI calls with different whitespace.
# Replace the two brittle exact-string checks in the source patch with
# one anchored, indentation-preserving substitution per screen.
if len(sys.argv)>2 and sys.argv[2] == 'windows':
    import re
    for name in ('ronda second AI','edit second AI'):
        pattern = (r"s=one\(s,\"      photoPath: photoPath,\\n      technicianContext: technicianContext,\","+
                   r"\s*\"      photoPath: photoPath,\\n      secondPhotoPath: secondPhotoPath,\\n      technicianContext: technicianContext,\",'"+
                   name+r"'\)")
        replacement = """
m=re.search(r'(?m)^([ \\t]*)photoPath:[ \\t]*photoPath,[ \\t]*with tempfile.TemporaryDirectory(prefix='auditar_ronda_patch_') as tmp:
    target=Path(tmp)/'ronda_ui.py'
    target.write_text(script,encoding='utf-8')
    original=sys.argv
    try:
        sys.argv=[str(target),*original[1:]]
        runpy.run_path(str(target),run_name='__main__')
    finally:sys.argv=original
print('AUDITAR_RONDA_UI_BUNDLE_APPLIED')
,s)
if m is None:
    raise RuntimeError('""" + name + """ photoPath binding absent')
indent=m.group(1)
s=s[:m.start()]+indent+'photoPath: photoPath,\\\\n'+indent+'secondPhotoPath: secondPhotoPath,'+s[m.end():]
"""
        script,n=re.subn(pattern,lambda _:replacement,script,count=1)
        if n!=1:
            raise RuntimeError('cannot adapt '+name+' for Windows')
with tempfile.TemporaryDirectory(prefix='auditar_ronda_patch_') as tmp:
    target=Path(tmp)/'ronda_ui.py'
    target.write_text(script,encoding='utf-8')
    original=sys.argv
    try:
        sys.argv=[str(target),*original[1:]]
        runpy.run_path(str(target),run_name='__main__')
    finally:sys.argv=original
print('AUDITAR_RONDA_UI_BUNDLE_APPLIED')
