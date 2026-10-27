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
        print('uso: patch_ai_action_plan_v3298.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / 'pubspec.yaml').exists():
        print(f'raiz inválida: {root}', file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    payload = (here / 'patch_ai_action_plan_v3298.part1').read_text(encoding='utf-8').strip()
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
        if '3.29.7' in text:
            home.write_text(text.replace('3.29.7', '3.29.8'), encoding='utf-8')

    required = [
        ('pubspec.yaml', 'version: 3.29.8+151'),
        ('lib/screens/report_screen.dart', 'Gerar plano de ação com IA'),
        ('lib/screens/ai_action_plan_review_screen.dart', 'Plano de ação sugerido pela IA'),
        ('lib/services/ai_assistant_service.dart', "'ncId': action.ncId ?? ''"),
        ('lib/services/pdf_service.dart', 'Evidência principal'),
        ('painel_web_google_apps_script/Code.gs', 'actionPlanSuggestions'),
    ]
    for rel, marker in required:
        path = root / rel
        if not path.exists() or marker not in path.read_text(encoding='utf-8'):
            raise RuntimeError(f'v3.29.8 não aplicada em {rel}: {marker}')

    report = (root / 'lib/screens/report_screen.dart').read_text(encoding='utf-8')
    for marker in (
        'Atualize o módulo de IA do Code.gs para a v3.29.8',
        'Nada é gravado automaticamente',
        'AiActionPlanReviewScreen',
    ):
        if marker not in report:
            raise RuntimeError(f'fluxo do plano IA ausente: {marker}')

    pdf = (root / 'lib/services/pdf_service.dart').read_text(encoding='utf-8')
    if 'if (includeActionPlanInPdf && executive)' not in pdf:
        raise RuntimeError('plano executivo não preservado')
    if "if (!executive && includeActionPlanInPdf)" not in pdf:
        raise RuntimeError('plano final do relatório completo ausente')

    code = (root / 'painel_web_google_apps_script/Code.gs').read_text(encoding='utf-8')
    for marker in (
        "mode === 'report_conclusion' ? 3400",
        'Não determine interdição formal automaticamente',
        'suggestedDeadlineDays',
    ):
        if marker not in code:
            raise RuntimeError(f'backend IA não atualizado: {marker}')

    print('v3.29.8: plano de ação por IA e fotos no executivo aplicados com sucesso')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
