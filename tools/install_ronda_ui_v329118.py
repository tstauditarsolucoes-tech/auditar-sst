#!/usr/bin/env python3
"""Install the Ronda recovery patch; tolerate Windows whitespace differences."""
import base64, gzip, runpy, sys, tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
blob=(root/'build_sources/v3.29.118-ronda-reports/patch_ronda_ui_v329118.py.gz.b64').read_text(encoding='utf-8').strip()
script=gzip.decompress(base64.b64decode(blob)).decode('utf-8')
if len(sys.argv)>2 and sys.argv[2]=='windows':
    start_marker='s=one(s,"      photoPath: photoPath,\\n      technicianContext: technicianContext,",'
    for tag in ('ronda second AI','edit second AI'):
        start=script.find(start_marker)
        if start<0: raise RuntimeError('Cannot locate '+tag+' source anchor')
        end_marker=",'"+tag+"')"
        end=script.find(end_marker,start)
        if end<0: raise RuntimeError('Cannot locate '+tag+' closing anchor')
        end+=len(end_marker)
        replacement=(
            "import re\n"
            "s,n=re.subn(r'(?m)^([ \\t]*)photoPath:[ \\t]*photoPath,[ \\t]*$', "
            "lambda m:m.group(1)+'photoPath: photoPath,'+chr(10)+"
            "m.group(1)+'secondPhotoPath: secondPhotoPath,',s,count=1)\n"
            "if n!=1: raise RuntimeError('Windows second photo binding absent')"
        )
        script=script[:start]+replacement+script[end:]
with tempfile.TemporaryDirectory(prefix='auditar_ronda_patch_') as tmp:
    target=Path(tmp)/'ronda_ui.py'
    target.write_text(script,encoding='utf-8')
    previous=sys.argv
    try:
        sys.argv=[str(target),*previous[1:]]
        runpy.run_path(str(target),run_name='__main__')
    finally:sys.argv=previous
print('AUDITAR_RONDA_UI_BUNDLE_APPLIED')
