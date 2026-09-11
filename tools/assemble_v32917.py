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

    # Base funcional oficial: v3.29.16+159.
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v32915.py')], check=True, cwd=repo, env=env)
    subprocess.run([sys.executable, str(repo / 'tools' / 'patch_quick_field_layout_v32916.py')], check=True, cwd=repo, env=env)

    # Somente as correções pontuais da v3.29.17.
    subprocess.run([sys.executable, str(repo / 'tools' / 'patch_v32917.py')], check=True, cwd=repo, env=env)

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    print(f'Fonte v3.29.17 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
