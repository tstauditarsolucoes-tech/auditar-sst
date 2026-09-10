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
        print('uso: patch_ai_report_chat_v3299.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / 'pubspec.yaml').exists():
        print(f'raiz inválida: {root}', file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    payload = (here / 'patch_ai_report_chat_v3299.part1').read_text(encoding='utf-8').strip()
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
        if '3.29.8' in text:
            home.write_text(text.replace('3.29.8', '3.29.9'), encoding='utf-8')

    required = [
        ('pubspec.yaml', 'version: 3.29.9+152'),
        ('lib/screens/report_screen.dart', 'AiReportReviewScreen'),
        ('lib/screens/ai_report_review_screen.dart', 'Converse com a IA sobre este relatório'),
        ('lib/screens/ai_report_review_screen.dart', 'Aponte os 3 erros mais graves'),
        ('lib/services/ai_assistant_service.dart', 'continueFinalReportReview'),
        ('lib/services/ai_assistant_service.dart', 'Evidência fotográfica repetida em itens diferentes'),
        ('painel_web_google_apps_script/Code.gs', "mode === 'report_review_chat'"),
        ('painel_web_google_apps_script/Code.gs', 'criticalFindings'),
        ('painel_web_google_apps_script/Code.gs', 'reportScore'),
    ]
    for rel, marker in required:
        path = root / rel
        if not path.exists() or marker not in path.read_text(encoding='utf-8'):
            raise RuntimeError(f'v3.29.9 não aplicada em {rel}: {marker}')

    report = (root / 'lib/screens/report_screen.dart').read_text(encoding='utf-8')
    for marker in (
        'Avaliar relatório com IA',
        'Gerar plano de ação com IA',
        'AiActionPlanReviewScreen',
        'AiReportReviewScreen',
    ):
        if marker not in report:
            raise RuntimeError(f'fluxo de relatório perdido: {marker}')

    pdf = (root / 'lib/services/pdf_service.dart').read_text(encoding='utf-8')
    for marker in ('Evidência principal', 'if (!executive && includeActionPlanInPdf)'):
        if marker not in pdf:
            raise RuntimeError(f'recurso de PDF perdido: {marker}')

    weekly = root / 'painel_web_google_apps_script/WeeklyReport.gs'
    if not weekly.exists() or 'setupWeeklyReportAuditar' not in weekly.read_text(encoding='utf-8'):
        raise RuntimeError('relatório semanal da v3.29.7 foi perdido')

    print('v3.29.9: revisão crítica interativa por IA aplicada com sucesso')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
