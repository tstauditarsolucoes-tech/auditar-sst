#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import io
import subprocess
import sys
import tarfile
from pathlib import Path

OVERLAY_SHA = '942763feac9c3a57bd7352dd534a68191efd8f56e04f826a5a99fbe52fbb98ef'
OVERLAY_PARTS = 10
OVERLAY_PART_SIZE = 16000
OVERLAY_LAST_PART_SIZE = 7696
PART09_SHA = 'bfdec8d6feaacc2d354a8eebb7a75c27a68cb53a1a8ad9ded46417f165d0f48c'
BASE64_ALPHABET = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='


def _repair_one_missing_char(raw: str, target_sha: str) -> str | None:
    raw_bytes = raw.encode('ascii')
    target = bytes.fromhex(target_sha)
    prefix = hashlib.sha256()
    for pos in range(len(raw_bytes) + 1):
        suffix = raw_bytes[pos:]
        for char in BASE64_ALPHABET:
            digest = prefix.copy()
            digest.update(bytes((char,)))
            digest.update(suffix)
            if digest.digest() == target:
                repaired = raw_bytes[:pos] + bytes((char,)) + suffix
                return repaired.decode('ascii')
        if pos < len(raw_bytes):
            prefix.update(raw_bytes[pos:pos + 1])
    return None


def _decode_overlay(repo: Path) -> bytes:
    parts = sorted((repo / 'tools').glob('v3500.overlay.part*.txt'))
    if len(parts) != OVERLAY_PARTS:
        raise RuntimeError(
            f'Overlay v3.35.0 incompleto: esperadas {OVERLAY_PARTS} partes; encontradas {len(parts)}.'
        )

    chunks: list[str] = []
    for index, part in enumerate(parts, start=1):
        raw = ''.join(part.read_text(encoding='utf-8').split())
        expected = OVERLAY_LAST_PART_SIZE if index == OVERLAY_PARTS else OVERLAY_PART_SIZE

        if index == 9 and len(raw) == expected - 1:
            repaired = _repair_one_missing_char(raw, PART09_SHA)
            if repaired is None:
                raise RuntimeError('Overlay v3.35.0 parte 09 incompleta e não foi possível reconstruir o caractere ausente.')
            raw = repaired
            print('Overlay v3.35.0 parte 09 reconstruída com validação SHA256.')

        if len(raw) < expected:
            raise RuntimeError(
                f'Overlay v3.35.0 parte {index:02d} incompleta: esperado ao menos {expected}; recebido {len(raw)}.'
            )
        chunks.append(raw[:expected])

    encoded = ''.join(chunks)
    data = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(data).hexdigest()
    if digest != OVERLAY_SHA:
        raise RuntimeError(f'Overlay v3.35.0 inválido: SHA256 {digest}.')
    return data


def _extract_overlay(app: Path, data: bytes) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        for member in members:
            name = member.name.replace('\\', '/')
            if name.startswith('/') or name.startswith('../') or '/..' in name:
                raise RuntimeError(f'Caminho inseguro no overlay: {member.name}')
        archive.extractall(app, filter='data')


def _validate(app: Path) -> None:
    pubspec = (app / 'pubspec.yaml').read_text(encoding='utf-8')
    if 'version: 3.35.0+153' not in pubspec:
        raise RuntimeError('Versão v3.35.0+153 não aplicada.')

    db = (app / 'lib' / 'database.dart').read_text(encoding='utf-8')
    models = (app / 'lib' / 'models.dart').read_text(encoding='utf-8')
    home = (app / 'lib' / 'screens' / 'home_screen.dart').read_text(encoding='utf-8')
    field = (app / 'lib' / 'screens' / 'field_quick_screen.dart').read_text(encoding='utf-8')
    new_inspection = (app / 'lib' / 'screens' / 'new_inspection_screen.dart').read_text(encoding='utf-8')
    detail = (app / 'lib' / 'screens' / 'company_detail_screen.dart').read_text(encoding='utf-8')
    sync = (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8')
    signature = (app / 'lib' / 'screens' / 'signature_screen.dart').read_text(encoding='utf-8')
    ready = (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8')

    checks = {
        'company_units': 'company_units' in db and 'class CompanyUnit' in models,
        'unit_id inspection': "'unit_id': unitId" in models,
        'Central Auditar': 'Central Auditar' in home,
        'Campo rápido': 'FieldQuickScreen' in home and 'Vistoria avulsa' in field,
        'avulsa oculta': 'active: false' in field,
        'initial company': 'initialCompany' in new_inspection and 'fieldMode' in new_inspection,
        'ambiente empresa': 'Ambiente da empresa' in detail,
        'sync v2': "'syncProtocol': 2" in sync,
        'assinatura tela cheia': 'Assinar em tela cheia' in signature,
        'assinatura gov': "value: 'gov'" in signature,
        'assinatura none': "value: 'none'" in signature,
        'plano ação opcional': 'includeActionPlan' in signature,
        '44 checklists': ready.count('  ReadyChecklistDefinition(') == 44,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações ausentes: ' + ', '.join(missing))

    code = (app / 'painel_web_google_apps_script' / 'Code.gs').read_text(encoding='utf-8')
    multi = (app / 'painel_web_google_apps_script' / 'MultiUser.gs').read_text(encoding='utf-8')
    if 'company_units' not in code or 'company_units' not in multi:
        raise RuntimeError('Backend multi-CNPJ ausente.')


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3332.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    overlay = _decode_overlay(repo)
    _extract_overlay(app, overlay)
    _validate(app)

    print(f'Fonte v3.35.0 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
