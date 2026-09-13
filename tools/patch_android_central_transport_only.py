#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_android_central_transport_only.py <app_dir>', file=sys.stderr)
        return 2

    app = Path(sys.argv[1])
    pubspec = app / 'pubspec.yaml'
    web_config = app / 'lib/services/web_service_config.dart'

    pub = pubspec.read_text(encoding='utf-8')
    pub, n = re.subn(
        r'version:\s*3\.29\.34\+176',
        'version: 3.29.35+177',
        pub,
        count=1,
    )
    if n != 1:
        raise RuntimeError('versão Android base 3.29.34+176 não encontrada')
    pubspec.write_text(pub, encoding='utf-8')

    config = web_config.read_text(encoding='utf-8')
    old = """  /// Grava os valores permanentes no banco local antes de abrir o app.\n  /// Assim, todas as funções existentes continuam usando a mesma fonte de\n  /// configuração, inclusive Painel, CIPA, Drive e Assistente IA.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    await db.setSetting(\n      'management_panel_endpoint',\n      endpoint.trim(),\n    );\n    await db.setSetting(\n      'management_panel_sync_key',\n      syncKey.trim(),\n    );\n  }\n"""
    new = """  /// A configuração incorporada funciona apenas como bootstrap.\n  /// Valores já salvos no aparelho são preservados. Esta alteração é interna\n  /// e não modifica nenhuma tela, estrutura ou layout do Android.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    final savedEndpoint = (await db.getSetting(\n      'management_panel_endpoint',\n      fallback: '',\n    )).trim();\n    final savedSyncKey = (await db.getSetting(\n      'management_panel_sync_key',\n      fallback: '',\n    )).trim();\n\n    if (savedEndpoint.isEmpty) {\n      await db.setSetting('management_panel_endpoint', endpoint.trim());\n    }\n    if (savedSyncKey.isEmpty) {\n      await db.setSetting('management_panel_sync_key', syncKey.trim());\n    }\n  }\n"""
    if config.count(old) != 1:
        raise RuntimeError('bloco de configuração embutida não encontrado')
    web_config.write_text(config.replace(old, new, 1), encoding='utf-8')

    print('Android v3.29.35+177: correção interna aplicada sem alterar UI/layout.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
