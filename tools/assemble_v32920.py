#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v32919.py')],
        check=True,
        cwd=repo,
        env=env,
    )
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_v32920_dual_storage.py')],
        check=True,
        cwd=repo,
        env=env,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    print(f'Fonte v3.29.20 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
