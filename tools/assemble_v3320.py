#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent

    # Monta exatamente a base estável v3.29.3 antes de aplicar as novas IAs.
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3293.py')],
        cwd=repo,
        check=True,
    )

    parts = [
        repo / 'tools' / 'v3320.patch.gz.b64.part00',
        repo / 'tools' / 'v3320.patch.gz.b64.part01',
        repo / 'tools' / 'v3320.patch.gz.b64.part02',
        repo / 'tools' / 'v3320.patch.gz.b64.part03',
    ]
    encoded = ''.join(path.read_text(encoding='utf-8').strip() for path in parts)
    patch_bytes = gzip.decompress(base64.b64decode(encoded))
    patch_file = repo / 'tools' / '.v3320.generated.patch'
    patch_file.write_bytes(patch_bytes)

    subprocess.run(
        ['git', 'apply', '--whitespace=nowarn', str(patch_file)],
        cwd=repo,
        check=True,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    pubspec = (app / 'pubspec.yaml').read_text(encoding='utf-8')
    if 'version: 3.32.0+148' not in pubspec:
        raise RuntimeError('A versão v3.32.0+148 não foi aplicada.')

    required = [
        app / 'lib' / 'screens' / 'dds_ai_screen.dart',
        app / 'lib' / 'screens' / 'prevention_ai_screen.dart',
    ]
    for path in required:
        if not path.exists():
            raise RuntimeError(f'Arquivo obrigatório ausente: {path}')

    print(f'Fonte v3.32.0 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
