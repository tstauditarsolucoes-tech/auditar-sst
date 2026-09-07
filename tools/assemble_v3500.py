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
PART_SHA = {
    1: '594cfa540c2a5243c7bdbf83625b44a829b21ab15f9231bcd9dc6f05163f0acd',
    2: 'bcddf3d8d7554b20261ad551b40b7b626f9649bcd6b81d7fdff51d0366d4ba75',
    3: 'd4077d4a9f2d123053f62412d836e33830fe69176dbffb616e052d1764e6c3ef',
    4: '1e3f1172804224299665fda407b32acd745e5e70471133b4af5c8847d5c58147',
    5: 'da76571fae6786557dc8cd95db8c0265f690434e97191c2fdfa1d24ed42ef1af',
    6: 'd948f0f79266e1dabbb7bf9e67e306af71601ac44bd1373727feafbe1b72c5f9',
    7: '4b6a332a5be94e5886b70cef05837c62f9f04fa99acb615cb50fc7935da19cb7',
    8: 'ad33eb2fa6f61b7cacf4fe99ca9c89c7a15a4a6f66bac85ff5bf9c1762b3285f',
    9: 'bfdec8d6feaacc2d354a8eebb7a75c27a68cb53a1a8ad9ded46417f165d0f48c',
    10: 'f8abb2b4d653b11c46f97efa783bf27022c3da5986775eb89a2c8da2b963492d',
}
BASE64_ALPHABET = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='


def _sha(raw: str) -> str:
    return hashlib.sha256(raw.encode('ascii')).hexdigest()


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
                return (raw_bytes[:pos] + bytes((char,)) + suffix).decode('ascii')
        if pos < len(raw_bytes):
            prefix.update(raw_bytes[pos:pos + 1])
    return None


def _repair_extra_contiguous_block(raw: str, expected: int, target_sha: str) -> str | None:
    extra = len(raw) - expected
    if extra <= 0:
        return None

    head = raw[:expected]
    if _sha(head) == target_sha:
        return head
    tail = raw[-expected:]
    if _sha(tail) == target_sha:
        return tail

    for pos in range(expected + 1):
        candidate = raw[:pos] + raw[pos + extra:]
        if len(candidate) == expected and _sha(candidate) == target_sha:
            return candidate
    return None


def _normalize_part(index: int, raw: str, expected: int) -> str:
    target_sha = PART_SHA[index]

    if len(raw) == expected and _sha(raw) == target_sha:
        return raw

    repaired: str | None = None
    if len(raw) > expected:
        repaired = _repair_extra_contiguous_block(raw, expected, target_sha)
    elif len(raw) == expected - 1:
        repaired = _repair_one_missing_char(raw, target_sha)

    if repaired is None:
        raise RuntimeError(
            f'Overlay v3.35.0 parte {index:02d} inválida: '
            f'tamanho {len(raw)} (esperado {expected}), SHA256 {_sha(raw)}.'
        )

    if len(repaired) != expected or _sha(repaired) != target_sha:
        raise RuntimeError(f'Falha interna ao reconstruir overlay parte {index:02d}.')

    print(f'Overlay v3.35.0 parte {index:02d} reconstruída com validação SHA256.')
    return repaired


def _exact_part03_from_helpers(repo: Path) -> str | None:
    helpers = [repo / 'tools' / f'v3500.part03.exact{i:02d}.txt' for i in range(1, 5)]
    if not all(path.exists() for path in helpers):
        return None
    raw = ''.join(''.join(path.read_text(encoding='utf-8').split()) for path in helpers)
    if len(raw) == OVERLAY_PART_SIZE and _sha(raw) == PART_SHA[3]:
        return raw
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

        if index == 3 and (len(raw) != expected or _sha(raw) != PART_SHA[3]):
            exact = _exact_part03_from_helpers(repo)
            if exact is not None:
                raw = exact
                print('Overlay v3.35.0 parte 03 restaurada pela referência exata.')

        chunks.append(_normalize_part(index, raw, expected))

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
