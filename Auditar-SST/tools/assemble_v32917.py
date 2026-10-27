#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repair_v32916_script(repo: Path) -> None:
    """Corrige somente um literal quebrado já existente no script da v3.29.16.

    A base funcional continua sendo v3.29.16+159; este reparo apenas torna o
    processo de montagem executável no runner Windows, sem alterar a lógica do app.
    """
    path = repo / 'tools' / 'patch_quick_field_layout_v32916.py'
    text = path.read_text(encoding='utf-8')
    bad = """        \"appBar: AppBar(title: const Text('Nova vistoria')),\n\",\n"""
    good = """        \"appBar: AppBar(title: const Text('Nova vistoria')),\\n\",\n"""
    if bad in text:
        path.write_text(text.replace(bad, good, 1), encoding='utf-8')

    subprocess.run(
        [sys.executable, '-m', 'py_compile', str(path)],
        check=True,
        cwd=repo,
    )


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'

    # Base funcional oficial: v3.29.16+159.
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v32915.py')],
        check=True,
        cwd=repo,
        env=env,
    )
    _repair_v32916_script(repo)
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_quick_field_layout_v32916.py')],
        check=True,
        cwd=repo,
        env=env,
    )

    # Somente as correções pontuais da v3.29.17.
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'patch_v32917.py')],
        check=True,
        cwd=repo,
        env=env,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    print(f'Fonte v3.29.17 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
