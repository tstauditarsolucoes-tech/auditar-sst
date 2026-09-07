#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

V340_SHA = '35be7a5355aec6727d159067b8895393ce45762556472caed38cc227cc6ecdc8'
V340_FAILED_OVERLAY_SHA = '6dcfe1c0fbc0a0a00c84a8086d5a56e03386e7a334cb011e851e25e5b90886f4'
V350_SHA = '0900962027afb85e6fcf7b9f4ac2580a11957c9c2b6da2f8e7d4c3d1b7fe5437'

EXPECTED_V340_REJECTS = {
    'lib/database.dart',
    'lib/models.dart',
    'lib/screens/companies_screen.dart',
    'lib/screens/new_inspection_screen.dart',
    'lib/services/pgr_service.dart',
}


def _patch_executable() -> str:
    found = shutil.which('patch')
    if found:
        return found

    if os.name == 'nt':
        candidates = [
            Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'Git' / 'usr' / 'bin' / 'patch.exe',
            Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Git' / 'usr' / 'bin' / 'patch.exe',
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

    raise RuntimeError('Utilitário patch não encontrado no ambiente de build.')


def _decode_parts(repo: Path, pattern: str, expected_parts: int, expected_sha: str) -> bytes:
    parts = sorted((repo / 'tools').glob(pattern))
    if len(parts) != expected_parts:
        raise RuntimeError(f'{pattern}: esperadas {expected_parts} partes; encontradas {len(parts)}')
    encoded = ''.join(p.read_text(encoding='utf-8').strip() for p in parts)
    data = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha:
        raise RuntimeError(f'{pattern}: SHA256 inválido {digest}')
    return data


def _apply_patch_bytes(work_app: Path, patch_bytes: bytes, *, allow_known_rejects: bool) -> None:
    patch_path = work_app.parent / '.assemble.tmp.patch'
    patch_path.write_bytes(gzip.decompress(patch_bytes))
    try:
        command = [
            _patch_executable(),
            '-p1',
            '--forward',
            '--batch',
            '--fuzz=3' if allow_known_rejects else '--fuzz=0',
            '-i',
            str(patch_path),
        ]
        result = subprocess.run(command, cwd=work_app, check=False)

        reject_files = sorted(work_app.rglob('*.rej'))
        reject_targets = {
            str(path.relative_to(work_app)).replace('\\', '/')[:-4]
            for path in reject_files
        }

        if allow_known_rejects:
            unexpected = reject_targets - EXPECTED_V340_REJECTS
            if unexpected:
                raise RuntimeError(
                    'Patch v3.34 rejeitou arquivos inesperados: ' + ', '.join(sorted(unexpected))
                )
            if result.returncode not in (0, 1):
                raise RuntimeError(f'Patch v3.34 falhou com código {result.returncode}.')
        else:
            if result.returncode != 0 or reject_files:
                raise RuntimeError('Patch v3.35 não aplicou integralmente sobre a base v3.34 corrigida.')
    finally:
        patch_path.unlink(missing_ok=True)


def _apply_v340_failed_overlay(repo: Path, work_app: Path) -> None:
    overlay = _decode_parts(
        repo,
        'v3400.failed-overlay.part*.txt',
        5,
        V340_FAILED_OVERLAY_SHA,
    )

    with tarfile.open(fileobj=io.BytesIO(overlay), mode='r:gz') as archive:
        files = {member.name.replace('\\', '/').lstrip('./') for member in archive.getmembers() if member.isfile()}
        if files != EXPECTED_V340_REJECTS:
            raise RuntimeError(
                'Overlay v3.34 contém arquivos inesperados: ' + ', '.join(sorted(files))
            )
        archive.extractall(work_app, filter='data')

    for reject in work_app.rglob('*.rej'):
        reject.unlink(missing_ok=True)
    for original in work_app.rglob('*.orig'):
        original.unlink(missing_ok=True)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3332.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    # A montagem ocorre em uma cópia temporária. A base validada v3.33.2 só é
    # substituída depois que v3.34 e v3.35 passam por todas as validações.
    with tempfile.TemporaryDirectory(prefix='auditar_v350_') as tmp:
        work_app = Path(tmp) / 'app'
        shutil.copytree(app, work_app)

        # O snapshot produzido pelo CI diverge da cópia histórica v3.33.2 em
        # cinco arquivos. Aplicamos todos os trechos compatíveis da v3.34 e,
        # somente nesses cinco arquivos conhecidos, restauramos a versão exata
        # da etapa v3.34 antes de seguir. Assim não há merge silencioso nem
        # alteração fora do conjunto auditado.
        v340_patch = _decode_parts(repo, 'v3400.patch.part*.txt', 11, V340_SHA)
        _apply_patch_bytes(work_app, v340_patch, allow_known_rejects=True)
        _apply_v340_failed_overlay(repo, work_app)

        pub340 = (work_app / 'pubspec.yaml').read_text(encoding='utf-8')
        if 'version: 3.34.0+152' not in pub340:
            raise RuntimeError('Base v3.34.0+152 não ficou íntegra após a correção de montagem.')
        if 'company_units' not in (work_app / 'lib' / 'database.dart').read_text(encoding='utf-8'):
            raise RuntimeError('Estrutura multi-CNPJ ausente após montagem da v3.34.')
        if 'class CompanyUnit' not in (work_app / 'lib' / 'models.dart').read_text(encoding='utf-8'):
            raise RuntimeError('Modelo CompanyUnit ausente após montagem da v3.34.')

        v350_patch = _decode_parts(repo, 'v3500.patch.part*.txt', 5, V350_SHA)
        _apply_patch_bytes(work_app, v350_patch, allow_known_rejects=False)

        pubspec = (work_app / 'pubspec.yaml').read_text(encoding='utf-8')
        if 'version: 3.35.0+153' not in pubspec:
            raise RuntimeError('Versão v3.35.0+153 não aplicada.')

        db = (work_app / 'lib' / 'database.dart').read_text(encoding='utf-8')
        models = (work_app / 'lib' / 'models.dart').read_text(encoding='utf-8')
        home = (work_app / 'lib' / 'screens' / 'home_screen.dart').read_text(encoding='utf-8')
        field = (work_app / 'lib' / 'screens' / 'field_quick_screen.dart').read_text(encoding='utf-8')
        new_inspection = (work_app / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8')
        detail = (work_app / 'lib' / 'screens' / 'company_detail_screen.dart').read_text(encoding='utf-8')
        sync = (work_app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8')

        checks = {
            'company_units': 'company_units' in db and 'class CompanyUnit' in models,
            'unit_id inspection': "'unit_id': unitId" in models,
            'Central Auditar': 'Central Auditar' in home,
            'Campo rápido': 'FieldQuickScreen' in home and 'Vistoria avulsa' in field,
            'avulsa oculta': 'active: false' in field,
            'initial company': 'initialCompany' in new_inspection and 'fieldMode' in new_inspection,
            'ambiente empresa': 'Ambiente da empresa' in detail,
            'sync v2': "'syncProtocol': 2" in sync,
            '44 checklists': (work_app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
        }
        missing = [name for name, ok in checks.items() if not ok]
        if missing:
            raise RuntimeError('Validações ausentes: ' + ', '.join(missing))

        code = (work_app / 'painel_web_google_apps_script' / 'Code.gs').read_text(encoding='utf-8')
        multi = (work_app / 'painel_web_google_apps_script' / 'MultiUser.gs').read_text(encoding='utf-8')
        if 'company_units' not in code or 'company_units' not in multi:
            raise RuntimeError('Backend multi-CNPJ ausente.')

        shutil.rmtree(app)
        shutil.copytree(work_app, app)

    print(f'Fonte v3.35.0 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
