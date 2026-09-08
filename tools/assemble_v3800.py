#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v3710.py')], cwd=repo, check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    overrides = repo / 'version_overrides' / 'v3800'

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.37.1+158', 'version: 3.38.0+159', 'versão 3.38.0')
    pub.write_text(text, encoding='utf-8')

    shutil.copy2(
        overrides / 'lib' / 'services' / 'extinguisher_inventory_service.dart',
        app / 'lib' / 'services' / 'extinguisher_inventory_service.dart',
    )
    shutil.copy2(
        overrides / 'lib' / 'screens' / 'extinguisher_stock_screen.dart',
        app / 'lib' / 'screens' / 'extinguisher_stock_screen.dart',
    )
    shutil.copy2(
        overrides / 'lib' / 'screens' / 'extinguishers_hub_screen.dart',
        app / 'lib' / 'screens' / 'extinguishers_hub_screen.dart',
    )

    p = app / 'lib' / 'screens' / 'extinguishers_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "class ExtinguishersScreen extends StatefulWidget {\n  final Company company;\n\n  const ExtinguishersScreen({\n    super.key,\n    required this.company,\n  });",
        "class ExtinguishersScreen extends StatefulWidget {\n  final Company company;\n  final bool embedded;\n\n  const ExtinguishersScreen({\n    super.key,\n    required this.company,\n    this.embedded = false,\n  });",
        'modo embutido da tela de extintores',
    )
    text = replace_once(
        text,
        "      appBar: AppBar(\n        title: const Text('Extintores'),",
        "      appBar: widget.embedded\n          ? null\n          : AppBar(\n        title: const Text('Extintores'),",
        'AppBar embutida',
    )
    p.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'company_detail_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "import 'extinguishers_screen.dart';",
        "import 'extinguishers_hub_screen.dart';",
        'import do hub de extintores',
    )
    text = replace_once(
        text,
        "subtitle: 'Cadastro, validade, vistoria e responsabilidade',\n            onTap: () => _open(ExtinguishersScreen(company: widget.company)),",
        "subtitle: 'Instalados, estoque, movimentações, validade e responsabilidade',\n            onTap: () => _open(ExtinguishersHubScreen(company: widget.company)),",
        'atalho de extintores',
    )
    p.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8').replace('versão 3.37.1', 'versão 3.38.0')
    p.write_text(text, encoding='utf-8')

    print(f'Fonte v3.38.0 Estoque de Extintores montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
