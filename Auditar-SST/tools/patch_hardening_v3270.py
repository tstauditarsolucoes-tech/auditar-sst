#!/usr/bin/env python3
from __future__ import annotations
import base64,gzip,subprocess,sys,tempfile
from pathlib import Path

def main():
    if len(sys.argv)!=2:
        print("uso: patch_hardening_v3270.py <raiz-do-app>",file=sys.stderr); return 2
    root=Path(sys.argv[1]).resolve()
    if not (root/"pubspec.yaml").exists():
        print(f"raiz inválida: {root}",file=sys.stderr); return 2
    here=Path(__file__).resolve().parent
    parts=[]
    for i in range(1,10):
        part=here/f"patch_hardening_v3270.part{i}"
        if not part.exists(): break
        parts.append(part.read_text().strip())
    if not parts:
        print("payload da v3.27.0 ausente",file=sys.stderr); return 2
    diff=gzip.decompress(base64.b64decode("".join(parts)))
    with tempfile.NamedTemporaryFile(suffix=".diff",delete=False) as f:
        f.write(diff); name=f.name
    try:
        subprocess.run(["git","apply","--unsafe-paths","--whitespace=nowarn",name],cwd=root,check=True)
    finally:
        Path(name).unlink(missing_ok=True)

    # Compatibilidade Flutter: ListView não possui construtor const.
    audit=root/"lib/screens/audit_trail_screen.dart"
    if audit.exists():
        text=audit.read_text()
        text=text.replace("? const ListView(", "? ListView(")
        audit.write_text(text)

    print("v3.27.0 aplicada com sucesso")
    return 0
if __name__=="__main__": raise SystemExit(main())
