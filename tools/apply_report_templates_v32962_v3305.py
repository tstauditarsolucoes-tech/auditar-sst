#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print('uso: apply_report_templates_v32962_v3305.py <raiz-do-app> <android|windows>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    platform = sys.argv[2].strip().lower()
    if platform not in {'android', 'windows'}:
        raise RuntimeError('plataforma deve ser android ou windows')
    if not (root / 'pubspec.yaml').exists():
        raise RuntimeError(f'raiz inválida: {root}')

    repo = Path(
        subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=root,
            text=True,
        ).strip()
    ).resolve()
    relative_root = root.relative_to(repo).as_posix()

    critical = [
        root / 'lib/services/sync_coordinator.dart',
        root / 'lib/services/device_sync_service.dart',
        root / 'lib/services/apps_script_http.dart',
    ]
    before = {path: digest(path) for path in critical if path.exists()}

    here = Path(__file__).resolve().parent
    parts = []
    for index in range(1, 10):
        part = here / f'report_templates_v32962_v3305.part{index}'
        if not part.exists():
            break
        parts.append(part.read_text(encoding='utf-8').strip())
    if not parts:
        raise RuntimeError('payload dos modelos de relatório ausente')

    diff = gzip.decompress(base64.b64decode(''.join(parts)))
    with tempfile.NamedTemporaryFile(suffix='.diff', delete=False) as tmp:
        tmp.write(diff)
        patch_path = Path(tmp.name)
    try:
        subprocess.run(
            [
                'git', 'apply', '--unsafe-paths', '--whitespace=nowarn',
                f'--directory={relative_root}', str(patch_path),
            ],
            cwd=repo,
            check=True,
        )
    finally:
        patch_path.unlink(missing_ok=True)

    pub = root / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    if platform == 'android':
        expected, new = 'version: 3.29.61+203', 'version: 3.29.62+204'
    else:
        expected, new = 'version: 3.30.4+191', 'version: 3.30.5+192'
    if expected not in text:
        current = next((line for line in text.splitlines() if line.startswith('version:')), 'version:?')
        raise RuntimeError(f'versão esperada ausente: {expected}; atual={current}')
    pub.write_text(text.replace(expected, new, 1), encoding='utf-8', newline='\n')

    after = {path: digest(path) for path in before}
    changed = [str(path) for path in before if before[path] != after[path]]
    if changed:
        raise RuntimeError('sincronização alterada indevidamente: ' + ', '.join(changed))

    report = (root / 'lib/screens/report_screen.dart').read_text(encoding='utf-8')
    pdf = (root / 'lib/services/pdf_service.dart').read_text(encoding='utf-8')
    for token in (
        'Padrão Auditar', 'Executivo', 'Fotográfico', 'Obra', 'Técnico Clean', 'NR-12',
        'report_template_user_default', 'report_template_company_', 'Personalizar modelo',
    ):
        if token not in report:
            raise RuntimeError(f'checagem da tela de relatório falhou: {token}')
    for token in (
        'effectiveTemplateId', 'showCover', 'showPhotos', 'showSignatures',
        'reportHeaderTitle', 'customFooter', '_templateCoverTitle',
    ):
        if token not in pdf:
            raise RuntimeError(f'checagem do PDF falhou: {token}')

    print(
        f'REPORT_TEMPLATES_OK platform={platform} '
        f'version={new.split()[1]} sync_critical_unchanged={len(before)}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
