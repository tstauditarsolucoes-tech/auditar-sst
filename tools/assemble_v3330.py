#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED_GZIP_SHA256 = 'de1071f767cec1209569d6289808ee4ef3f7e1ad54243234c2eb878c7f71a1fe'
EXPECTED_PARTS = 8


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3320.py')],
        cwd=repo,
        check=True,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    parts = sorted((repo / 'tools').glob('v3330.patch.part*.txt'))
    if len(parts) != EXPECTED_PARTS:
        raise RuntimeError(f'Esperadas {EXPECTED_PARTS} partes do patch v3.33.0; encontradas {len(parts)}.')
    encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
    compressed = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(compressed).hexdigest()
    if digest != EXPECTED_GZIP_SHA256:
        raise RuntimeError(f'Patch v3.33.0 inválido: SHA256 {digest}')

    patch_bytes = gzip.decompress(compressed)
    patch_path = repo / 'tools' / '.v3330.patch.tmp'
    patch_path.write_bytes(patch_bytes)
    try:
        subprocess.run(
            ['git', 'apply', '-p1', '--whitespace=nowarn', str(patch_path)],
            cwd=app,
            check=True,
        )
    finally:
        patch_path.unlink(missing_ok=True)

    pubspec = (app / 'pubspec.yaml').read_text(encoding='utf-8')
    if 'version: 3.33.0+149' not in pubspec:
        raise RuntimeError('A versão v3.33.0+149 não foi aplicada.')

    sync = (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8')
    if "'syncProtocol': 2" not in sync or 'baseServerVersion' not in sync:
        raise RuntimeError('Protocolo de sincronização v2 ausente.')
    if 'hasPendingLocalEdit' not in sync:
        raise RuntimeError('Proteção de edição local pendente ausente.')

    code = (app / 'painel_web_google_apps_script' / 'Code.gs').read_text(encoding='utf-8')
    multi = (app / 'painel_web_google_apps_script' / 'MultiUser.gs').read_text(encoding='utf-8')
    if 'pcOwnsMaster' in code or 'pcOwnsMaster' in multi:
        raise RuntimeError('Regra antiga de preferência do Windows ainda presente.')
    if 'bootstrapConflict' not in code or 'bootstrapConflict' not in multi:
        raise RuntimeError('Conciliação de bootstrap ausente.')

    print(f'Fonte v3.33.0 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
