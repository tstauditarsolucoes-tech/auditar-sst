#!/usr/bin/env python3
from pathlib import Path
import re
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: esperado 1 bloco, encontrado {count}')
    return text.replace(old, new, 1)


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
    settings = app / 'lib/screens/settings_screen.dart'

    for path in (pubspec, web_config, settings):
        if not path.exists():
            raise FileNotFoundError(path)

    pub = pubspec.read_text(encoding='utf-8')
    pub = update_version(pub, target)
    pubspec.write_text(pub, encoding='utf-8')

    config = web_config.read_text(encoding='utf-8')
    old_apply = """  /// Grava os valores permanentes no banco local antes de abrir o app.\n  /// Assim, todas as funções existentes continuam usando a mesma fonte de\n  /// configuração, inclusive Painel, CIPA, Drive e Assistente IA.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    await db.setSetting(\n      'management_panel_endpoint',\n      endpoint.trim(),\n    );\n    await db.setSetting(\n      'management_panel_sync_key',\n      syncKey.trim(),\n    );\n  }\n"""
    new_apply = """  /// Usa a configuração incorporada somente como bootstrap.\n  ///\n  /// A URL/chave gravadas pelo usuário nunca são sobrescritas na inicialização.\n  /// Isso permite recuperar a Central Online quando uma implantação /exec antiga\n  /// deixa de existir (HTTP 404), sem reinstalar o aplicativo e sem perder dados.\n  static Future<void> applyEmbeddedConfiguration() async {\n    if (!isEmbedded) return;\n\n    final db = AppDatabase.instance;\n    final savedEndpoint = (await db.getSetting(\n      'management_panel_endpoint',\n      fallback: '',\n    ))\n        .trim();\n    final savedSyncKey = (await db.getSetting(\n      'management_panel_sync_key',\n      fallback: '',\n    ))\n        .trim();\n\n    if (savedEndpoint.isEmpty) {\n      await db.setSetting(\n        'management_panel_endpoint',\n        endpoint.trim(),\n      );\n    }\n    if (savedSyncKey.isEmpty) {\n      await db.setSetting(\n        'management_panel_sync_key',\n        syncKey.trim(),\n      );\n    }\n  }\n"""
    config = replace_once(config, old_apply, new_apply, 'web_service_config.dart')
    web_config.write_text(config, encoding='utf-8')

    screen = settings.read_text(encoding='utf-8')

    old_block = """          if (WebServiceConfig.isEmbedded)\n            const Card(\n              child: Padding(\n                padding: EdgeInsets.all(14),\n                child: Row(\n                  crossAxisAlignment: CrossAxisAlignment.start,\n                  children: [\n                    Icon(\n                      Icons.verified_rounded,\n                      color: Color(0xFF178A3D),\n                    ),\n                    SizedBox(width: 10),\n                    Expanded(\n                      child: Column(\n                        crossAxisAlignment: CrossAxisAlignment.start,\n                        children: [\n                          Text(\n                            'Central online configurada',\n                            style: TextStyle(fontWeight: FontWeight.w800),\n                          ),\n                          SizedBox(height: 5),\n                          Text(\n                            'A URL e a chave já vêm configuradas no aplicativo. Não é necessário preencher novamente ao atualizar ou instalar em outro aparelho.',\n                            style: TextStyle(fontSize: 12.5, height: 1.35),\n                          ),\n                        ],\n                      ),\n                    ),\n                  ],\n                ),\n              ),\n            )\n          else ...[\n            TextField(\n              controller: panelEndpoint,\n              keyboardType: TextInputType.url,\n              autocorrect: false,\n              decoration: const InputDecoration(\n                labelText: 'URL do Google Apps Script',\n                hintText: 'https://script.google.com/macros/s/.../exec',\n                prefixIcon: Icon(Icons.language_rounded),\n              ),\n            ),\n            const SizedBox(height: 12),\n            TextField(\n              controller: panelSyncKey,\n              obscureText: true,\n              autocorrect: false,\n              enableSuggestions: false,\n              decoration: const InputDecoration(\n                labelText: 'Chave de sincronização',\n                hintText: 'Chave criada na configuração do painel',\n                prefixIcon: Icon(Icons.key_rounded),\n              ),\n            ),\n            const SizedBox(height: 8),\n            const Card(\n              child: Padding(\n                padding: EdgeInsets.all(12),\n                child: Row(\n                  crossAxisAlignment: CrossAxisAlignment.start,\n                  children: [\n                    Icon(Icons.info_outline_rounded),\n                    SizedBox(width: 9),\n                    Expanded(\n                      child: Text(\n                        'Use sempre a URL permanente da implantação, terminada em /exec. Não copie links script.googleusercontent.com, porque eles são temporários e podem expirar.',\n                        style: TextStyle(fontSize: 12.5),\n                      ),\n                    ),\n                  ],\n                ),\n              ),\n            ),\n            const SizedBox(height: 10),\n            FilledButton.icon(\n              onPressed: _save,\n              icon: const Icon(Icons.save_outlined),\n              label: const Text('Salvar painel web'),\n            ),\n          ],\n"""

    new_block = """          if (WebServiceConfig.isEmbedded)\n            const Card(\n              child: Padding(\n                padding: EdgeInsets.all(14),\n                child: Row(\n                  crossAxisAlignment: CrossAxisAlignment.start,\n                  children: [\n                    Icon(\n                      Icons.verified_rounded,\n                      color: Color(0xFF178A3D),\n                    ),\n                    SizedBox(width: 10),\n                    Expanded(\n                      child: Column(\n                        crossAxisAlignment: CrossAxisAlignment.start,\n                        children: [\n                          Text(\n                            'Central online configurada',\n                            style: TextStyle(fontWeight: FontWeight.w800),\n                          ),\n                          SizedBox(height: 5),\n                          Text(\n                            'A URL e a chave iniciais vêm configuradas no aplicativo. Elas podem ser substituídas abaixo quando a implantação do Apps Script mudar.',\n                            style: TextStyle(fontSize: 12.5, height: 1.35),\n                          ),\n                        ],\n                      ),\n                    ),\n                  ],\n                ),\n              ),\n            ),\n          if (WebServiceConfig.isEmbedded) ...[\n            const SizedBox(height: 8),\n            const Text(\n              'Se a Central Online retornar HTTP 404, cole abaixo a URL permanente /exec da implantação atual e salve. A nova configuração permanecerá neste dispositivo.',\n              style: TextStyle(fontSize: 12.5, color: Colors.black54),\n            ),\n            const SizedBox(height: 12),\n          ],\n          TextField(\n            controller: panelEndpoint,\n            keyboardType: TextInputType.url,\n            autocorrect: false,\n            decoration: const InputDecoration(\n              labelText: 'URL do Google Apps Script',\n              hintText: 'https://script.google.com/macros/s/.../exec',\n              prefixIcon: Icon(Icons.language_rounded),\n            ),\n          ),\n          const SizedBox(height: 12),\n          TextField(\n            controller: panelSyncKey,\n            obscureText: true,\n            autocorrect: false,\n            enableSuggestions: false,\n            decoration: const InputDecoration(\n              labelText: 'Chave de sincronização',\n              hintText: 'Chave criada na configuração do painel',\n              prefixIcon: Icon(Icons.key_rounded),\n            ),\n          ),\n          const SizedBox(height: 8),\n          const Card(\n            child: Padding(\n              padding: EdgeInsets.all(12),\n              child: Row(\n                crossAxisAlignment: CrossAxisAlignment.start,\n                children: [\n                  Icon(Icons.info_outline_rounded),\n                  SizedBox(width: 9),\n                  Expanded(\n                    child: Text(\n                      'Use sempre a URL permanente da implantação, terminada em /exec. Não copie links script.googleusercontent.com, porque eles são temporários e podem expirar.',\n                      style: TextStyle(fontSize: 12.5),\n                    ),\n                  ),\n                ],\n              ),\n            ),\n          ),\n          const SizedBox(height: 10),\n          FilledButton.icon(\n            onPressed: _save,\n            icon: const Icon(Icons.save_outlined),\n            label: const Text('Salvar painel web'),\n          ),\n"""

    screen = replace_once(screen, old_block, new_block, 'settings_screen.dart')
    settings.write_text(screen, encoding='utf-8')

    version = 'v3.29.38+180' if target == 'windows' else 'v3.29.35+177'
    print(f'Patch {version} aplicado: Central Online recuperável após HTTP 404.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
