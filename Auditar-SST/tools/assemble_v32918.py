#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'

    # Mantém v3.29.17 como base imediata e, por consequência, v3.29.16
    # como base funcional oficial. A v3.36.1 não participa da montagem.
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v32917.py')],
        check=True,
        cwd=repo,
        env=env,
    )
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_v32918.py')],
        check=True,
        cwd=repo,
        env=env,
    )
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_v32918_interactive.py')],
        check=True,
        cwd=repo,
        env=env,
    )
    # Correção final do loading dinâmico do chat Executivo.
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_v32918_constfix.py')],
        check=True,
        cwd=repo,
        env=env,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    print(f'Fonte v3.29.18 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
