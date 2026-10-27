#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v32913.py')], check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_executive_report_v32914.py'), str(app)],
        check=True,
        env=env,
    )
    print(f'Fonte v3.29.14 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
