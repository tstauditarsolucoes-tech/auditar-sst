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

    config = web_config.read_text(encoding='utf-8')
    old_apply = """  /// Grava os valores permanentes no banco local antes de abrir o app.\n  /// Assim, todas as funções existentes continuam usando a mesma fonte de\n  /// configuração, inclusive Painel, CIPA, Drive e Assistente IA.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    await db.setSetting(\n      'management_panel_endpoint',\n      endpoint.trim(),\n    );\n    await db.setSetting(\n      'management_panel_sync_key',\n      syncKey.trim(),\n    );\n  }\n"""
    new_apply = """  /// Usa a configuração incorporada somente como bootstrap.\n  /// Valores já gravados no dispositivo não são sobrescritos na inicialização.\n  /// Esta alteração é interna e não modifica telas, estrutura ou layout.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    final savedEndpoint = (await db.getSetting(\n      'management_panel_endpoint',\n      fallback: '',\n    )).trim();\n    final savedSyncKey = (await db.getSetting(\n      'management_panel_sync_key',\n      fallback: '',\n    )).trim();\n\n    if (savedEndpoint.isEmpty) {\n      await db.setSetting('management_panel_endpoint', endpoint.trim());\n    }\n    if (savedSyncKey.isEmpty) {\n      await db.setSetting('management_panel_sync_key', syncKey.trim());\n    }\n  }\n"""

    count = config.count(old_apply)
    if count != 1:
        raise RuntimeError(
            f'web_service_config.dart: esperado 1 bloco, encontrado {count}'
        )
    web_config.write_text(
        config.replace(old_apply, new_apply, 1),
        encoding='utf-8',
    )

    version = 'v3.29.38+180' if target == 'windows' else 'v3.29.35+177'
    print(
        f'Patch {version} aplicado somente em configuração interna; UI preservada.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
