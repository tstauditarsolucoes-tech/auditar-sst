#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_pending_improvements_v3295.py <raiz-do-app>', file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    payload = ''.join(
        (here / name).read_text(encoding='utf-8').strip()
        for name in ['patch_pending_improvements_v3295.part1']
    )
    source = gzip.decompress(base64.b64decode(payload)).decode('utf-8')

    with tempfile.NamedTemporaryFile('w', suffix='.py', encoding='utf-8', delete=False) as tmp:
        tmp.write(source)
        temp_path = Path(tmp.name)
    try:
        subprocess.run([sys.executable, str(temp_path), sys.argv[1]], check=True)
    finally:
        temp_path.unlink(missing_ok=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
