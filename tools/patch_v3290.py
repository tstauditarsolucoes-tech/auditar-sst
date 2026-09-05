#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import sys
import tarfile
from pathlib import Path

EXPECTED = {
    "lib/database.dart",
    "lib/models.dart",
    "lib/screens/home_screen.dart",
    "lib/screens/new_inspection_screen.dart",
    "lib/screens/report_screen.dart",
    "lib/screens/signature_screen.dart",
    "lib/services/auth_service.dart",
    "lib/services/pdf_service.dart",
    "lib/services/report_file_service.dart",
    "pubspec.yaml",
}


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: patch_v3290.py <raiz-do-app>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / "pubspec.yaml").exists():
        print(f"raiz inválida: {root}", file=sys.stderr)
        return 2

    payload_path = Path(__file__).resolve().parent / "v3290_payload.b64"
    if not payload_path.exists():
        print("payload v3.29.0 ausente", file=sys.stderr)
        return 2

    raw = base64.b64decode(payload_path.read_text(encoding="utf-8").strip(), validate=True)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = [m for m in archive.getmembers() if m.isfile()]
        names = {m.name for m in members}
        if names != EXPECTED:
            missing = sorted(EXPECTED - names)
            extra = sorted(names - EXPECTED)
            raise RuntimeError(f"payload inesperado; ausentes={missing}; extras={extra}")

        for member in members:
            rel = Path(member.name)
            if rel.is_absolute() or ".." in rel.parts:
                raise RuntimeError(f"caminho inválido no payload: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"arquivo ausente no payload: {member.name}")
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())

    required = {
        "pubspec.yaml": "version: 3.29.0+142",
        "lib/screens/signature_screen.dart": "Assinar externamente por Gov.br",
        "lib/screens/report_screen.dart": "Incluir plano de ação no relatório",
        "lib/services/pdf_service.dart": "O QUE FOI IDENTIFICADO",
        "lib/services/auth_service.dart": "purgeCompaniesOutsideAccess",
        "lib/screens/home_screen.dart": "versão 3.29.0",
        "lib/screens/new_inspection_screen.dart": "backgroundColor: Colors.white",
        "lib/database.dart": "report_signature_mode",
    }
    for rel, marker in required.items():
        text = (root / rel).read_text(encoding="utf-8")
        if marker not in text:
            raise RuntimeError(f"validação v3.29.0 falhou em {rel}: {marker}")

    signature = (root / "lib/screens/signature_screen.dart").read_text(encoding="utf-8")
    if "Emitir sem assinatura" not in signature:
        raise RuntimeError("emissão sem assinatura ausente")

    print("v3.29.0 consolidada aplicada com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
