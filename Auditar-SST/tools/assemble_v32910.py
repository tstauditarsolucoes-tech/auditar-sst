#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v3299.py')], check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_ai_transport_v32910.py'), str(app)],
        check=True,
    )
    print(f'Fonte v3.29.10 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
