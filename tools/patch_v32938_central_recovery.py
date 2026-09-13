#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: esperado 1 bloco, encontrado {count}')
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_v32938_central_recovery.py <app_dir>', file=sys.stderr)
        return 2

    app = Path(sys.argv[1])
    pubspec = app / 'pubspec.yaml'
    web_config = app / 'lib/services/web_service_config.dart'
    settings = app / 'lib/screens/settings_screen.dart'

    for path in (pubspec, web_config, settings):
        if not path.exists():
            raise FileNotFoundError(path)

    # v3.29.38+180: mesma base funcional, correção pontual da recuperação da
    # Central Online. Nenhum layout mobile é redesenhado.
    pub = pubspec.read_text(encoding='utf-8')
    pub, n = re.subn(r'version:\s*3\.29\.37\+179', 'version: 3.29.38+180', pub, count=1)
    if n != 1:
        raise RuntimeError('pubspec: versão 3.29.37+179 não encontrada')
    pubspec.write_text(pub, encoding='utf-8')

    config = web_config.read_text(encoding='utf-8')
    old_apply = """  /// Grava os valores permanentes no banco local antes de abrir o app.\n  /// Assim, todas as funções existentes continuam usando a mesma fonte de\n  /// configuração, inclusive Painel, CIPA, Drive e Assistente IA.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    await db.setSetting(\n      'management_panel_endpoint',\n      endpoint.trim(),\n    );\n    await db.setSetting(\n      'management_panel_sync_key',\n      syncKey.trim(),\n    );\n  }\n"""
    new_apply = """  /// Usa a configuração incorporada somente como bootstrap.\n  ///\n  /// A URL/chave gravadas pelo usuário nunca são sobrescritas na inicialização.\n  /// Isso permite recuperar a Central Online quando uma implantação /exec antiga\n  /// deixa de existir (HTTP 404), sem reinstalar o aplicativo e sem perder dados.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    final savedEndpoint = (await db.getSetting(\n      'management_panel_endpoint',\n      fallback: '',\n    ))\n        .trim();\n    final savedSyncKey = (await db.getSetting(\n      'management_panel_sync_key',\n      fallback: '',\n    ))\n        .trim();\n\n    if (savedEndpoint.isEmpty) {\n      await db.setSetting(\n        'management_panel_endpoint',\n        endpoint.trim(),\n      );\n    }\n    if (savedSyncKey.isEmpty) {\n      await db.setSetting(\n        'management_panel_sync_key',\n        syncKey.trim(),\n      );\n    }\n  }\n"""
    config = replace_once(config, old_apply, new_apply, 'web_service_config.dart')
    web_config.write_text(config, encoding='utf-8')

    screen = settings.read_text(encoding='utf-8')

    # O bloco anterior escondia os campos quando havia configuração embutida.
    # Isso impedia trocar uma URL /exec que passou a responder 404.
    pattern = re.compile(
        r"          if \(WebServiceConfig\.isEmbedded\)\n"
        r"            const Card\((?P<card>.*?)\n"
        r"            \)\n"
        r"          else \.\.\.\[\n"
        r"            TextField\(\n"
        r"              controller: panelEndpoint,(?P<fields>.*?)\n"
        r"          const SizedBox\(height: 28\),",
        re.S,
    )
    match = pattern.search(screen)
    if not match:
        raise RuntimeError('settings_screen.dart: bloco da Central Online não encontrado')

    card_body = match.group('card')
    fields_tail = match.group('fields')

    replacement = (
        "          if (WebServiceConfig.isEmbedded)\n"
        "            const Card(" + card_body + "\n"
        "            ),\n"
        "          if (WebServiceConfig.isEmbedded) ...[\n"
        "            const SizedBox(height: 8),\n"
        "            const Text(\n"
        "              'A configuração incorporada é apenas inicial. Se a implantação do Apps Script mudar ou retornar 404, substitua a URL permanente /exec abaixo. A nova URL ficará salva neste dispositivo.',\n"
        "              style: TextStyle(fontSize: 12.5, color: Colors.black54),\n"
        "            ),\n"
        "            const SizedBox(height: 12),\n"
        "          ],\n"
        "          TextField(\n"
        "            controller: panelEndpoint," + fields_tail + "\n"
        "          const SizedBox(height: 28),"
    )
    screen = screen[:match.start()] + replacement + screen[match.end():]

    # Mensagem do cartão deixa claro que a configuração pode ser corrigida.
    screen = screen.replace(
        "'A URL e a chave já vêm configuradas no aplicativo. Não é necessário preencher novamente ao atualizar ou instalar em outro aparelho.'",
        "'A URL e a chave iniciais vêm configuradas no aplicativo. Elas podem ser substituídas abaixo quando a implantação do Apps Script mudar.'",
        1,
    )

    settings.write_text(screen, encoding='utf-8')

    print('Patch v3.29.38 aplicado: Central Online recuperável após HTTP 404.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
