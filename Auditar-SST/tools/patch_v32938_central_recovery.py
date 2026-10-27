#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def update_version(pub: str, target: str) -> str:
    if target == 'windows':
        source = r'version:\s*3\.29\.37\+179'
        replacement = 'version: 3.29.38+180'
        expected = '3.29.37+179'
    elif target == 'android':
        source = r'version:\s*3\.29\.34\+176'
        replacement = 'version: 3.29.35+177'
        expected = '3.29.34+176'
    else:
        raise RuntimeError(f'alvo inválido: {target}')

    pub, n = re.subn(source, replacement, pub, count=1)
    if n != 1:
        raise RuntimeError(f'pubspec: versão {expected} não encontrada')
    return pub


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print(
            'uso: patch_v32938_central_recovery.py <app_dir> [windows|android]',
            file=sys.stderr,
        )
        return 2

    app = Path(sys.argv[1])
    target = sys.argv[2].lower() if len(sys.argv) == 3 else 'windows'
    pubspec = app / 'pubspec.yaml'
    web_config = app / 'lib/services/web_service_config.dart'

    for path in (pubspec, web_config):
        if not path.exists():
            raise FileNotFoundError(path)

    pub = update_version(pubspec.read_text(encoding='utf-8'), target)
    pubspec.write_text(pub, encoding='utf-8')

    # Mantém o comportamento estável que já funcionava nas versões anteriores:
    # a URL /exec e a chave incorporadas no build são gravadas novamente a cada
    # inicialização. Isso corrige instalações que ficaram com endpoint antigo ou
    # temporário salvo no banco local, sem mudar nenhuma tela ou layout.
    config = web_config.read_text(encoding='utf-8')
    required = [
        "await db.setSetting(\n      'management_panel_endpoint',\n      endpoint.trim(),\n    );",
        "await db.setSetting(\n      'management_panel_sync_key',\n      syncKey.trim(),\n    );",
    ]
    for marker in required:
        if marker not in config:
            raise RuntimeError('web_service_config.dart: configuração embutida permanente ausente')
    if 'savedEndpoint' in config or 'savedSyncKey' in config:
        raise RuntimeError('web_service_config.dart: bootstrap antigo ainda presente')

    version = 'v3.29.38+180' if target == 'windows' else 'v3.29.35+177'
    print(
        f'Patch {version} aplicado: Central embutida restaurada; UI preservada.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
