#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3331.py')],
        cwd=repo,
        check=True,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    patch = repo / 'tools' / 'v3332.patch'
    subprocess.run(
        ['git', 'apply', '-p1', '--whitespace=nowarn', str(patch)],
        cwd=app,
        check=True,
    )

    pubspec = (app / 'pubspec.yaml').read_text(encoding='utf-8')
    if 'version: 3.33.2+151' not in pubspec:
        raise RuntimeError('A versão v3.33.2+151 não foi aplicada.')

    home = (app / 'lib' / 'screens' / 'home_screen.dart').read_text(encoding='utf-8')
    if '_refresh(showLoading: false)' not in home:
        raise RuntimeError('Atualização silenciosa da tela inicial ausente.')
    if 'unawaited(_refresh(showLoading: false))' not in home:
        raise RuntimeError('Recebimento silencioso da sincronização ausente.')

    sync = (app / 'lib' / 'services' / 'sync_coordinator.dart').read_text(encoding='utf-8')
    required = (
        'ValueNotifier<int> _indicatorRevision',
        'ValueListenableBuilder<int>',
        'StackFit.expand',
        'RepaintBoundary(child: widget.child)',
    )
    for marker in required:
        if marker not in sync:
            raise RuntimeError(f'Proteção visual da sincronização ausente: {marker}')

    status_start = sync.find('void _setDesktopStatus')
    status_end = sync.find('void _handleConnectivity', status_start)
    if status_start < 0 or status_end < 0:
        raise RuntimeError('Bloco de status da sincronização não localizado.')
    if 'setState' in sync[status_start:status_end]:
        raise RuntimeError('O status da sincronização ainda reconstrói a tela inteira.')

    if "'syncProtocol': 2" not in (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8'):
        raise RuntimeError('Sincronização bidirecional v3.33.0 foi perdida.')

    print(f'Fonte v3.33.2 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
