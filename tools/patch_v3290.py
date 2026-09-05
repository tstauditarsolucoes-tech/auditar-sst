#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: patch_v3290.py <raiz-do-app>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not (root / "pubspec.yaml").exists():
        print(f"raiz inválida: {root}", file=sys.stderr)
        return 2

    payload = Path(__file__).resolve().parent / "patch_v3290.part1"
    if not payload.exists():
        print("payload final da v3.29.0 ausente", file=sys.stderr)
        return 2

    diff = gzip.decompress(base64.b64decode(payload.read_text(encoding="utf-8").strip()))
    with tempfile.NamedTemporaryFile(suffix=".diff", delete=False) as f:
        f.write(diff)
        patch_name = f.name

    try:
        subprocess.run(
            ["git", "apply", "--unsafe-paths", "--whitespace=nowarn", patch_name],
            cwd=root,
            check=True,
        )
    finally:
        Path(patch_name).unlink(missing_ok=True)

    required = {
        "pubspec.yaml": "version: 3.29.0+142",
        "lib/screens/signature_screen.dart": "Assinar externamente por Gov.br",
        "lib/screens/report_screen.dart": "Incluir plano de ação",
        "lib/services/pdf_service.dart": "O QUE FOI IDENTIFICADO",
        "lib/services/auth_service.dart": "purgeCompaniesOutsideAccess",
        "lib/screens/home_screen.dart": "versão 3.29.0",
    }
    for rel, marker in required.items():
        text = (root / rel).read_text(encoding="utf-8")
        if marker not in text:
            raise RuntimeError(f"validação v3.29.0 falhou em {rel}: {marker}")

    print("v3.29.0 aplicada sobre a base v3.27.0 com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
