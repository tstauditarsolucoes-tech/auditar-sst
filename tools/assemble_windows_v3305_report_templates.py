#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: assemble_windows_v3305_report_templates.py <raiz-do-app>', file=sys.stderr)
        return 2

    repo = Path(__file__).resolve().parent.parent
    root_arg = Path(sys.argv[1])
    root = root_arg if root_arg.is_absolute() else (repo / root_arg)
    root = root.resolve()

    subprocess.run(
        [sys.executable, str(repo / 'tools/assemble_windows_v3304_ronda_latest.py'), str(root)],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo / 'tools/apply_report_templates_v32962_v3305.py'), str(root), 'windows'],
        cwd=repo,
        check=True,
    )

    pubspec = (root / 'pubspec.yaml').read_text(encoding='utf-8')
    if 'version: 3.30.5+192' not in pubspec:
        raise RuntimeError('versão Windows v3.30.5+192 não foi aplicada')

    print('WINDOWS_V3305_REPORT_TEMPLATES_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
