#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import sys
import tarfile
from pathlib import Path


def _safe_extract(archive: tarfile.TarFile, root: Path) -> None:
    root = root.resolve()
    for member in archive.getmembers():
        target = (root / member.name).resolve()
        if target != root and root not in target.parents:
            raise RuntimeError(f"caminho inválido no payload: {member.name}")
    archive.extractall(root)


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: patch_v3290.py <raiz-do-app>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / "pubspec.yaml").exists():
        print(f"raiz inválida: {root}", file=sys.stderr)
        return 2

    payload_file = Path(__file__).resolve().parent / "v3290_full.b64"
    if not payload_file.exists():
        print(f"payload ausente: {payload_file.name}", file=sys.stderr)
        return 2

    try:
        encoded = "".join(payload_file.read_text(encoding="utf-8").split())
        payload = base64.b64decode(encoded, validate=True)
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            _safe_extract(archive, root)
    except Exception as exc:
        raise RuntimeError(f"falha ao aplicar payload robusto v3.29.0: {exc}") from exc

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
        path = root / rel
        if not path.exists():
            raise RuntimeError(f"validação v3.29.0 falhou: arquivo ausente {rel}")
        text = path.read_text(encoding="utf-8")
        if marker not in text:
            raise RuntimeError(f"validação v3.29.0 falhou em {rel}: {marker}")

    signature = (root / "lib/screens/signature_screen.dart").read_text(encoding="utf-8")
    if "Emitir sem assinatura" not in signature:
        raise RuntimeError("emissão sem assinatura ausente")

    database = (root / "lib/database.dart").read_text(encoding="utf-8")
    if "include_action_plan" not in database:
        raise RuntimeError("campo include_action_plan ausente")

    print("v3.29.0 consolidada aplicada com sucesso (payload robusto)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
