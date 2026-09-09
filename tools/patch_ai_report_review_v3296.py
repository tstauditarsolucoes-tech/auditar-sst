#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import subprocess
import sys
import tempfile
from pathlib import Path


def _apply_inside_app(root: Path, patch_name: str) -> None:
    repo_top = Path(
        subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=root,
            text=True,
        ).strip()
    ).resolve()
    relative_root = root.relative_to(repo_top).as_posix()
    subprocess.run(
        [
            'git',
            'apply',
            '--unsafe-paths',
            '--whitespace=nowarn',
            f'--directory={relative_root}',
            patch_name,
        ],
        cwd=repo_top,
        check=True,
    )


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_ai_report_review_v3296.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / 'pubspec.yaml').exists():
        print(f'raiz inválida: {root}', file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    payload = ''.join(
        (here / f'patch_ai_report_review_v3296.part{i}').read_text(encoding='utf-8').strip()
        for i in range(1, 6)
    )
    diff = gzip.decompress(base64.b64decode(payload))

    with tempfile.NamedTemporaryFile(suffix='.diff', delete=False) as tmp:
        tmp.write(diff)
        patch_path = Path(tmp.name)
    try:
        _apply_inside_app(root, str(patch_path))
    finally:
        patch_path.unlink(missing_ok=True)

    home = root / 'lib/screens/home_screen.dart'
    if home.exists():
        text = home.read_text(encoding='utf-8')
        if '3.29.5' in text:
            home.write_text(text.replace('3.29.5', '3.29.6'), encoding='utf-8')

    required = [
        ('pubspec.yaml', 'version: 3.29.6+149'),
        ('lib/screens/report_screen.dart', 'Avaliar relatório com IA'),
        ('lib/services/ai_assistant_service.dart', 'reviewFinalReport'),
        ('lib/database.dart', 'updateInspectionNarrative'),
    ]
    for rel, marker in required:
        if marker not in (root / rel).read_text(encoding='utf-8'):
            raise RuntimeError(f'v3.29.6 não aplicada em {rel}: {marker}')

    report = (root / 'lib/screens/report_screen.dart').read_text(encoding='utf-8')
    for marker in (
        'Revisão final com IA',
        'Verificações automáticas',
        'Aplicar conclusão da IA',
        'Manter relatório original',
    ):
        if marker not in report:
            raise RuntimeError(f'recurso de revisão IA ausente: {marker}')

    ai = (root / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
    for marker in (
        'Pendência sem local exato',
        'Prazo de ação vencido',
        'Item marcado como Conforme precisa de conferência',
        "'mode': 'report_conclusion'",
    ):
        if marker not in ai:
            raise RuntimeError(f'validação do relatório ausente: {marker}')

    print('v3.29.6 revisão final do relatório com IA aplicada com sucesso')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
