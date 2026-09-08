#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v3700.py')], cwd=repo, check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.37.0+157', 'version: 3.37.1+158', 'versão 3.37.1')
    pub.write_text(text, encoding='utf-8')

    pgr = app / 'lib' / 'screens' / 'pgr_screen.dart'
    text = pgr.read_text(encoding='utf-8')

    text = replace_once(
        text,
        "title: const Text('Arquivar este PGR?'),",
        "title: const Text('Remover este PGR?'),",
        'título da confirmação de remoção',
    )
    text = replace_once(
        text,
        "'“${current['title'] ?? 'PGR'}” deixará de aparecer como PGR ativo. As análises e o histórico serão preservados.',",
        "'“${current['title'] ?? 'PGR'}” será removido da lista de PGRs cadastrados. O histórico interno será preservado para segurança dos dados.',",
        'texto da confirmação de remoção',
    )
    text = replace_once(
        text,
        "child: const Text('Arquivar'),",
        "child: const Text('Remover'),",
        'botão do diálogo',
    )
    text = replace_once(
        text,
        "    await AppDatabase.instance.deactivatePgrDocument('${current['id']}');\n    document = null;\n    await _load();",
        "    setState(() => busy = true);\n    try {\n      await AppDatabase.instance.deactivatePgrDocument('${current['id']}');\n      document = null;\n      await _load();\n      _message('PGR removido da lista de cadastrados.');\n    } catch (e) {\n      _message('Não foi possível remover o PGR: $e', error: true);\n    } finally {\n      if (mounted) setState(() => busy = false);\n    }",
        'remoção segura do PGR',
    )
    text = replace_once(
        text,
        "if (document != null && documents.length > 1)\n                      TextButton.icon(\n                        onPressed: busy ? null : _deactivateCurrent,\n                        icon: const Icon(Icons.archive_outlined),\n                        label: const Text('Arquivar'),\n                      ),",
        "if (document != null)\n                      TextButton.icon(\n                        onPressed: busy ? null : _deactivateCurrent,\n                        icon: const Icon(Icons.delete_outline_rounded),\n                        style: TextButton.styleFrom(foregroundColor: Colors.red.shade700),\n                        label: const Text('Remover PGR'),\n                      ),",
        'botão Remover PGR sempre visível',
    )

    pgr.write_text(text, encoding='utf-8')

    home = app / 'lib' / 'screens' / 'home_screen.dart'
    text = home.read_text(encoding='utf-8')
    text = text.replace('versão 3.37.0', 'versão 3.37.1')
    home.write_text(text, encoding='utf-8')

    print(f'Fonte v3.37.1 com remoção de PGR montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
