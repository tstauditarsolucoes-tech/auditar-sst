#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v32915.py')],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_campo_rapido_ia_v32916.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    print(f'Fonte v3.29.16 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
