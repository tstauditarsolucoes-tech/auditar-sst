#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import subprocess
import sys
import tarfile
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent

    # Monta exatamente a base estável v3.29.3 antes de sobrepor apenas
    # os arquivos alterados nas versões 3.30/3.31/3.32.
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3293.py')],
        cwd=repo,
        check=True,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    parts = [repo / 'tools' / f'v3320.overlay.b64.part{i:02d}' for i in range(11)]
    missing = [str(path) for path in parts if not path.exists()]
    if missing:
        raise RuntimeError(f'Partes do overlay ausentes: {missing}')

    encoded = ''.join(path.read_text(encoding='utf-8').strip() for path in parts)
    archive_bytes = base64.b64decode(encoded)

    # Extrai o overlay somente dentro da pasta do app.
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:gz') as tf:
        app_root = app.resolve()
        for member in tf.getmembers():
            target = (app / member.name).resolve()
            if app_root != target and app_root not in target.parents:
                raise RuntimeError(f'Caminho inválido no overlay: {member.name}')
        tf.extractall(app)

    pubspec = (app / 'pubspec.yaml').read_text(encoding='utf-8')
    if 'version: 3.32.0+148' not in pubspec:
        raise RuntimeError('A versão v3.32.0+148 não foi aplicada.')

    required = [
        app / 'lib' / 'screens' / 'dds_ai_screen.dart',
        app / 'lib' / 'screens' / 'prevention_ai_screen.dart',
        app / 'lib' / 'services' / 'ai_assistant_service.dart',
    ]
    for path in required:
        if not path.exists():
            raise RuntimeError(f'Arquivo obrigatório ausente: {path}')

    print(f'Fonte v3.32.0 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
