#!/usr/bin/env python3
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

FORBIDDEN = [
    'Auditar SST',
    'AUDITAR SST',
    'Auditar Soluções',
    'Auditar Solucoes',
    'auditarsolucoes@gmail.com',
    '3221-1549',
    'tstauditarsolucoes',
    'br.com.auditar',
    'Central de Gestão Auditar',
    'Central de Gestao Auditar',
    'AuditarSstApp',
    'AuditarBrandLogo',
    'AuditarUser',
    'auditarBackgroundSyncDispatcher',
    'auditar_brand_logo',
    'auditar_sst',
    'auditar_atual',
    'auditar_executivo',
    'auditar_fotografico',
    'auditar_obra',
    'auditar_tecnico_clean',
    'auditar_nr12',
    'o Auditar',
]


def byte_needles():
    out = []
    for term in FORBIDDEN:
        for enc in ('utf-8', 'utf-16le', 'utf-16be'):
            out.append((term, enc, term.encode(enc)))
    return out

NEEDLES = byte_needles()


def scan_bytes(label: str, data: bytes, findings: list[str], depth: int = 0) -> None:
    low = data.lower()
    for term, enc, needle in NEEDLES:
        if needle.lower() in low:
            findings.append(f'{label}: {term} [{enc}]')
    if depth >= 2:
        return
    try:
        bio = io.BytesIO(data)
        if zipfile.is_zipfile(bio):
            bio.seek(0)
            with zipfile.ZipFile(bio) as zf:
                for info in zf.infolist():
                    if info.is_dir() or info.file_size > 180 * 1024 * 1024:
                        continue
                    try:
                        scan_bytes(f'{label}!{info.filename}', zf.read(info), findings, depth + 1)
                    except Exception:
                        pass
    except Exception:
        pass


def scan_path(path: Path, findings: list[str]) -> None:
    if path.is_dir():
        for child in path.rglob('*'):
            if child.is_file() and child.stat().st_size <= 180 * 1024 * 1024:
                try:
                    scan_bytes(str(child), child.read_bytes(), findings)
                except Exception:
                    pass
    elif path.is_file():
        scan_bytes(str(path), path.read_bytes(), findings)
    else:
        findings.append(f'CAMINHO_AUSENTE: {path}')


def main() -> int:
    if len(sys.argv) < 2:
        print('uso: scan_neutral_artifact_v1.py <arquivo-ou-diretorio> [...]', file=sys.stderr)
        return 2
    findings: list[str] = []
    for arg in sys.argv[1:]:
        scan_path(Path(arg), findings)
    unique = []
    seen = set()
    for item in findings:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    if unique:
        print('NEUTRAL_ARTIFACT_SCAN_FAIL')
        for item in unique[:120]:
            print(' -', item)
        return 1
    print('NEUTRAL_ARTIFACT_SCAN_OK: nenhuma referência proibida encontrada no artefato final.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
