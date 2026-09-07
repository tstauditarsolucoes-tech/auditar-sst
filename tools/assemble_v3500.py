#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import subprocess
import sys
from pathlib import Path

V340_SHA = '35be7a5355aec6727d159067b8895393ce45762556472caed38cc227cc6ecdc8'
V350_SHA = '0900962027afb85e6fcf7b9f4ac2580a11957c9c2b6da2f8e7d4c3d1b7fe5437'


def apply_parts(repo: Path, app: Path, pattern: str, expected_parts: int, expected_sha: str) -> None:
    parts = sorted((repo / 'tools').glob(pattern))
    if len(parts) != expected_parts:
        raise RuntimeError(f'{pattern}: esperadas {expected_parts} partes; encontradas {len(parts)}')
    encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
    compressed = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(compressed).hexdigest()
    if digest != expected_sha:
        raise RuntimeError(f'{pattern}: SHA256 inválido {digest}')
    patch_path = repo / 'tools' / '.assemble.tmp.patch'
    patch_path.write_bytes(gzip.decompress(compressed))
    try:
        subprocess.run(
            ['git', 'apply', '-p1', '--whitespace=nowarn', str(patch_path)],
            cwd=repo,
            check=True,
        )
    finally:
        patch_path.unlink(missing_ok=True)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3332.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    apply_parts(repo, app, 'v3400.patch.part*.txt', 11, V340_SHA)
    apply_parts(repo, app, 'v3500.patch.part*.txt', 5, V350_SHA)

    pubspec = (app / 'pubspec.yaml').read_text(encoding='utf-8')
    if 'version: 3.35.0+153' not in pubspec:
        raise RuntimeError('Versão v3.35.0+153 não aplicada. Pubspec atual: ' + pubspec.splitlines()[3])

    db = (app / 'lib' / 'database.dart').read_text(encoding='utf-8')
    models = (app / 'lib' / 'models.dart').read_text(encoding='utf-8')
    home = (app / 'lib' / 'screens' / 'home_screen.dart').read_text(encoding='utf-8')
    field = (app / 'lib' / 'screens' / 'field_quick_screen.dart').read_text(encoding='utf-8')
    new_inspection = (app / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8')
    detail = (app / 'lib' / 'screens' / 'company_detail_screen.dart').read_text(encoding='utf-8')
    sync = (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8')

    checks = {
        'company_units': 'company_units' in db and 'class CompanyUnit' in models,
        'unit_id inspection': "'unit_id': unitId" in models,
        'Central Auditar': 'Central Auditar' in home,
        'Campo rápido': 'FieldQuickScreen' in home and 'Vistoria avulsa' in field,
        'avulsa oculta': 'active: false' in field,
        'initial company': 'initialCompany' in new_inspection and 'fieldMode' in new_inspection,
        'ambiente empresa': 'Ambiente da empresa' in detail,
        'sync v2': "'syncProtocol': 2" in sync,
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações ausentes: ' + ', '.join(missing))

    code = (app / 'painel_web_google_apps_script' / 'Code.gs').read_text(encoding='utf-8')
    multi = (app / 'painel_web_google_apps_script' / 'MultiUser.gs').read_text(encoding='utf-8')
    if 'company_units' not in code or 'company_units' not in multi:
        raise RuntimeError('Backend multi-CNPJ ausente.')

    print(f'Fonte v3.35.0 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
