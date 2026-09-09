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
        print('uso: patch_weekly_report_v3297.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / 'pubspec.yaml').exists():
        print(f'raiz inválida: {root}', file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    payload = (here / 'patch_weekly_report_v3297.part1').read_text(encoding='utf-8').strip()
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
        if '3.29.6' in text:
            home.write_text(text.replace('3.29.6', '3.29.7'), encoding='utf-8')

    required = [
        ('pubspec.yaml', 'version: 3.29.7+150'),
        ('lib/models.dart', 'weeklyReportEnabled'),
        ('lib/database.dart', 'version: 21'),
        ('lib/screens/companies_screen.dart', 'Enviar relatório semanal'),
        ('lib/screens/companies_screen.dart', 'Dia do envio semanal'),
        ('lib/services/management_panel_service.dart', "'weeklyReport':"),
        ('lib/services/management_panel_service.dart', "'resolvedActions':"),
        ('lib/services/management_panel_service.dart', "'pendingActions':"),
        ('painel_web_google_apps_script/WeeklyReport.gs', 'setupWeeklyReportAuditar'),
        ('painel_web_google_apps_script/WeeklyReport.gs', 'O que continua pendente'),
    ]
    for rel, marker in required:
        path = root / rel
        if not path.exists() or marker not in path.read_text(encoding='utf-8'):
            raise RuntimeError(f'v3.29.7 não aplicada em {rel}: {marker}')

    print('v3.29.7 relatório semanal opcional aplicado com sucesso')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
