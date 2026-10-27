#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_signature_fullscreen_v3291.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    signature = root / 'lib/screens/signature_screen.dart'
    pubspec = root / 'pubspec.yaml'
    home = root / 'lib/screens/home_screen.dart'

    if not signature.exists() or not pubspec.exists() or not home.exists():
        fail('fonte do app incompleta para aplicar v3.29.1')

    text = signature.read_text(encoding='utf-8')

    if "import 'package:flutter/services.dart';" not in text:
        anchor = "import 'package:flutter/material.dart';"
        if anchor not in text:
            fail('import de material não encontrado')
        text = text.replace(
            anchor,
            anchor + "\nimport 'package:flutter/services.dart';",
            1,
        )

    if '_openFullScreenSignature({' not in text:
        anchor = '  Widget _signatureCard({' 
        if anchor not in text:
            fail('ponto de inserção do método de tela cheia não encontrado')

        method = r'''  Future<void> _openFullScreenSignature({
    required SignatureController controller,
    required String title,
  }) async {
    if (!mounted) return;

    final forceLandscape = Platform.isAndroid;
    if (forceLandscape) {
      await SystemChrome.setPreferredOrientations(const [
        DeviceOrientation.landscapeLeft,
        DeviceOrientation.landscapeRight,
      ]);
    }

    try {
      if (!mounted) return;
      await Navigator.of(context).push<void>(
        MaterialPageRoute(
          fullscreenDialog: true,
          builder: (_) => _FullScreenSignaturePage(
            title: title,
            controller: controller,
          ),
        ),
      );
    } finally {
      if (forceLandscape) {
        await SystemChrome.setPreferredOrientations(
          const <DeviceOrientation>[],
        );
      }
    }

    if (mounted) setState(() {});
  }

'''
        text = text.replace(anchor, method + anchor, 1)

    if "label: const Text('Assinar em tela cheia')" not in text:
        marker = '            OutlinedButton.icon(\n              onPressed: controller.clear,'
        if marker not in text:
            # tolerate formatter/manual layout differences
            marker = '            OutlinedButton.icon(\r\n              onPressed: controller.clear,'
        if marker not in text:
            fail('botão de limpar assinatura não encontrado')

        button = r'''            SizedBox(
              width: double.infinity,
              child: FilledButton.tonalIcon(
                onPressed: () => _openFullScreenSignature(
                  controller: controller,
                  title: title,
                ),
                icon: const Icon(Icons.fullscreen),
                label: const Text('Assinar em tela cheia'),
              ),
            ),
            const SizedBox(height: 8),
'''
        text = text.replace(marker, button + marker, 1)

    if 'class _FullScreenSignaturePage extends StatelessWidget' not in text:
        fullscreen_page = r'''

class _FullScreenSignaturePage extends StatelessWidget {
  final String title;
  final SignatureController controller;

  const _FullScreenSignaturePage({
    required this.title,
    required this.controller,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            children: [
              Row(
                children: [
                  IconButton(
                    tooltip: 'Voltar',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.arrow_back),
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Limpar assinatura',
                    onPressed: controller.clear,
                    icon: const Icon(Icons.delete_outline),
                  ),
                  const SizedBox(width: 6),
                  FilledButton.icon(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.check),
                    label: const Text('Concluir'),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(
                      color: Theme.of(context).colorScheme.outlineVariant,
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: LayoutBuilder(
                    builder: (context, constraints) => Signature(
                      controller: controller,
                      width: constraints.maxWidth,
                      height: constraints.maxHeight,
                      backgroundColor: Colors.white,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Assine com o dedo e toque em Concluir para voltar à vistoria.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12, color: Colors.black54),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
'''
        text = text.rstrip() + fullscreen_page + '\n'

    signature.write_text(text, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    if 'version: 3.29.1+143' not in pub:
        if 'version: 3.29.0+142' not in pub:
            fail('versão 3.29.0+142 não encontrada no pubspec')
        pub = pub.replace('version: 3.29.0+142', 'version: 3.29.1+143', 1)
        pubspec.write_text(pub, encoding='utf-8')

    home_text = home.read_text(encoding='utf-8')
    home_text = home_text.replace('versão 3.29.0', 'versão 3.29.1')
    home.write_text(home_text, encoding='utf-8')

    final_text = signature.read_text(encoding='utf-8')
    required = [
        "import 'package:flutter/services.dart';",
        'Assinar em tela cheia',
        'DeviceOrientation.landscapeLeft',
        'class _FullScreenSignaturePage extends StatelessWidget',
    ]
    for item in required:
        if item not in final_text:
            fail(f'validação v3.29.1 falhou: {item}')

    print('v3.29.1: assinatura em tela cheia/landscape restaurada no celular')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
