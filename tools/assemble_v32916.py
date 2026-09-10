#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v32915.py')], cwd=repo, check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    # v3.29.16: restaura a vistoria rápida/avulsa e o layout Central Auditar
    # sobre a linha atual estabilizada, sem substituir as funções de IA.
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_field_quick_layout_v32916.py'), str(app)],
        cwd=repo,
        check=True,
        env=env,
    )
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_v32916_layout_finalize.py'), str(app)],
        cwd=repo,
        check=True,
        env=env,
    )
    print(f'Fonte v3.29.16 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
